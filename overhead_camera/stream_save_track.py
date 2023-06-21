#Run the following commands to execute:
#python3 pub.py --endpoint aicgt013q5xy-ats.iot.us-east-1.amazonaws.com --ca_file root-CA.crt --cert GroundSystem.cert.pem  --key GroundSystem.private.key --client_id groundSysGps --topic groundsys/video --count 0
#python3 stream_save_track.py --key GroundSystem.private.key --cert GroundSystem.cert.pem --client_id groundSysVideo --topic groundsys/video --endpoint aicgt013q5xy-ats.iot.us-east-1.amazonaws.com --ca_file root-CA.crt --count 0

 #***DIRECT CAMERA STREAM IMPLEMENTATION

# Uses examples/video.py from pyvirtualcam repository for video streaming
# repo: https://github.com/letmaik/pyvirtualcam/blob/main/examples/video.py

# This script plays back a video file on the virtual camera.
# It also shows how to:
# - select a specific camera device
# - use BGR as pixel format

# modified to also save recording and stream to jitsi meeting

#sudo apt-get install python3-tk python3-dev
#***** run [sudo modprobe v4l2loopback devices=1] before running file
# sudo apt install v4l2loopback-dkms
# sudo modprobe v4l2loopback devices=1

import pyvirtualcam
from pyvirtualcam import PixelFormat
import cv2
from awscrt import mqtt
import sys
import threading
import time
from uuid import uuid4
import json
import utils.command_line_utils as command_line_utils

# ***MQTT functions copied over from implemented MQTT files in folder for integrated implementation
#from sub.py
cmdUtils = command_line_utils.CommandLineUtils("PubSub - Send and recieve messages through an MQTT connection.")
cmdUtils.add_common_mqtt_commands()
cmdUtils.add_common_topic_message_commands()
cmdUtils.add_common_proxy_commands()
cmdUtils.add_common_logging_commands()
cmdUtils.register_command("key", "<path>", "Path to your key in PEM format.", True, str)
cmdUtils.register_command("cert", "<path>", "Path to your client certificate in PEM format.", True, str)
cmdUtils.register_command("port", "<int>", "Connection port. AWS IoT supports 443 and 8883 (optional, default=auto).", type=int)
cmdUtils.register_command("client_id", "<str>", "Client ID to use for MQTT connection (optional, default='test-*').", default="test-" + str(uuid4()))
cmdUtils.register_command("count", "<int>", "The number of messages to send (optional, default='10').", default=10, type=int)
cmdUtils.register_command("is_ci", "<str>", "If present the sample will run in CI mode (optional, default='None')")

# Needs to be called so the command utils parse the commands
cmdUtils.get_args()

#from sub.py
received_count = 0
received_all_event = threading.Event()
is_ci = cmdUtils.get_command("is_ci", None) != None

rec_start = False #state of recording (if started, == true, else false)
released = True #state of whether recording has been closed after test ended (true == closed, else false)
rec_count = 0 #holds state of what test is currently going on to name recording accordingly
init_rec = False #state of whether recording has been initialized (true == initialized, else false)

#from sub.py
# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    print("Connection interrupted. error: {}".format(error))

#from sub.py
# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print("Connection resumed. return_code: {} session_present: {}".format(return_code, session_present))

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)

#from sub.py
def on_resubscribe_complete(resubscribe_future):
        resubscribe_results = resubscribe_future.result()
        print("Resubscribe results: {}".format(resubscribe_results))

        for topic, qos in resubscribe_results['topics']:
            if qos is None:
                sys.exit("Server rejected resubscribe to topic: {}".format(topic))

#from sub.py, modified to look for start stop command from UI and act accordingly
# Callback when the subscribed topic receives a message
def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    global rec_start, rec_count, released, init_rec
    print("Received message from topic '{}': {}".format(topic, payload))
    global received_count
    received_count += 1
    if received_count == cmdUtils.get_command("count"):
        received_all_event.set()

    #Start command sent, start new recording
    #if (payload==b'"start"'):
    if (payload == b'false'):
        rec_start = True
        released = False
        print("Starting track recording for test "+ str(rec_count) +"...")

    #Stop command sent, stop current recording
    #elif (payload==b'"stop"'):
    elif (payload == b'true'):
        rec_start = False
        init_rec = False
        print("Stopping track recording for test "+ str(rec_count) +"...")
        rec_count+=1
        
# main computation function, opens video stream, 
# creates and reroutes to virtual port, 
# saves to recording if in a test
def stream_and_save(video_path, device):
    global rec_start, rec_count, released, init_rec
   
    #open camera port video
    video = cv2.VideoCapture(video_path)

    if not video.isOpened():
        raise ValueError("error opening video")
    length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = video.get(cv2.CAP_PROP_FPS)

    #open virtual camera
    with pyvirtualcam.Camera(width, height, fps, fmt=PixelFormat.BGR,
                         device=device, print_fps=False) as cam:
        print(f'Virtual cam started: {cam.device} ({cam.width}x{cam.height} @ {cam.fps}fps)')

    # start frame streaming
        count = 0
        while True:
            # Restart video on last frame.
            if count == length:
                count = 0
                video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            # Read video frame.
            ret, frame = video.read()
            if not ret:
                raise RuntimeError('Error fetching frame')
            
            # resize so frame fits recording
            frame = cv2.resize(frame,(640,480))
            if rec_start == True:
                if init_rec == False:
                    video_name = 'recordings/stream'+str(rec_count)+ '.mp4' 
                    print("video " + video_name)
                    fourcc = cv2.VideoWriter_fourcc(*'MP4V')
                    rec_out = cv2.VideoWriter(video_name, fourcc, 20.0, (int(video.get(3)), int(video.get(4))))
                    init_rec = True
                rec_out.write(frame)

            # Wait for 'a' key to stop the program
                cv2.imshow('frame', frame)

            if rec_start == False:
                if released == False:
                    rec_out.release()
                    released = True
            

            # Send to virtual cam.
            cam.send(frame)

            # Wait until it's time for the next frame
            cam.sleep_until_next_frame()
            
            count += 1
        cv2.destroyAllWindows()


#if __name__ == '__main__':
video_path = "/dev/video0"  #original camera port
device = "/dev/video2"      #virtual camera port

#start mqtt
mqtt_connection = cmdUtils.build_mqtt_connection(on_connection_interrupted, on_connection_resumed)

if is_ci == False:
    print("Connecting to {} with client ID '{}'...".format(
        cmdUtils.get_command(cmdUtils.m_cmd_endpoint), cmdUtils.get_command("client_id")))
else:
    print("Connecting to endpoint with client ID")
connect_future = mqtt_connection.connect()

# Future.result() waits until a result is available
connect_future.result()
print("Connected!")

message_count = cmdUtils.get_command("count")
message_topic = cmdUtils.get_command(cmdUtils.m_cmd_topic)
message_string = cmdUtils.get_command(cmdUtils.m_cmd_message)

print("Subscribing to topic '{}'...".format(message_topic))
subscribe_future, packet_id = mqtt_connection.subscribe(
    topic=message_topic,
    qos=mqtt.QoS.AT_LEAST_ONCE,
    callback=on_message_received)

#Subscribe
subscribe_result = subscribe_future.result()
print("Subscribed with {}".format(str(subscribe_result['qos'])))

# start overhead camera tasks
stream_and_save(video_path, device)

# Wait for all messages to be received.
# This waits forever if count was set to 0.
if message_count != 0 and not received_all_event.is_set():
    print("Waiting for all messages to be received...")

received_all_event.wait()
print("{} message(s) received.".format(received_count))

# Disconnect
print("Disconnecting...")
disconnect_future = mqtt_connection.disconnect()
disconnect_future.result()
print("Disconnected!")

    
