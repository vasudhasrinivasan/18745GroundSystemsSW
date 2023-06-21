# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.

from awscrt import mqtt
import sys
import threading
import time
from uuid import uuid4
import json
import numpy as np
import math
from scipy.optimize import least_squares


# Parse arguments
import utils.command_line_utils as command_line_utils
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

received_count = 0
received_all_event = threading.Event()
is_ci = cmdUtils.get_command("is_ci", None) != None


"""
CONSTANTS
"""
ANCHOR_POINTS = [(0,0), (0,7), (7,7), (7,0)]    #Coordinates of anchor points (m)
ROUND_DIGITS = 5                                    #Number of digits to round to

"""
GLOBAL VARS
"""
prev_tag = [-1,-1]    # Keep track of previous tag position to calculate angle

"""
HELPER FUNCTIONS
"""

def residual(x, circles):
    err = []
    for (x0, y0), r in circles:
        err.append((x[0] - x0)**2 + (x[1] - y0)**2 - r**2)
    return err

def get_tag_coords(anchor_points, distances):
    # Define four circles
    circles = [(anchor_points[0], distances[0]), (anchor_points[1], distances[1]), (anchor_points[2], distances[2]), (anchor_points[3], distances[3])]

    # Find the intersection points using least squares method
    res = least_squares(residual, [0, 0], args=(circles,))
    points = [(round(res.x[0], ROUND_DIGITS), round(res.x[1], ROUND_DIGITS))]

    return points[0]
    
def get_tag_direction(tag):
    return math.degrees(math.atan((prev_tag[1] - tag[1])/(prev_tag[0] - tag[0])))

"""

FUNCTIONS

"""

def get_tag_info(distances):
    """
    Calculates tag position and degrees from previous position based on anchor point distances
    `distances`(list): Distance from each anchor point to the tag (m)
    
    Returns: ((x, y), deg)
    """
    tag = get_tag_coords(ANCHOR_POINTS, distances)
    deg = get_tag_direction(tag)
    prev_tag = tag  #update prev to new tag data
    return [tag, deg]
        
# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    print("Connection interrupted. error: {}".format(error))


# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print("Connection resumed. return_code: {} session_present: {}".format(return_code, session_present))

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)


def on_resubscribe_complete(resubscribe_future):
        resubscribe_results = resubscribe_future.result()
        print("Resubscribe results: {}".format(resubscribe_results))

        for topic, qos in resubscribe_results['topics']:
            if qos is None:
                sys.exit("Server rejected resubscribe to topic: {}".format(topic))


# Callback when the subscribed topic receives a message
def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    print(payload)
    global received_count
    received_count += 1
    if received_count == cmdUtils.get_command("count"):
        received_all_event.set()

    #Bottom left, top left, top right, bottom right.
    distances = [0.0, 7.0, 7.0*math.sqrt(2), 7.0] # recieve from mqtt

    received_data = json.loads(payload.decode('utf-8'))
    
    distances[0] = received_data["0x37EB"]
    distances[1] = received_data["0x37EC"]
    distances[2] = received_data["0x37ED"]
    distances[3] = received_data["0x37EF"]

    coordinate = get_tag_info(distances)
    data = {'x': coordinate[0][0], 'y': coordinate[0][1], 'degree': coordinate[1]}
    message_json = json.dumps(data)
    message_topic = "groundsys/gps"
    mqtt_connection.publish(
        topic=message_topic,
        payload=message_json,
        qos=mqtt.QoS.AT_LEAST_ONCE)

if __name__ == '__main__':
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

    # Subscribe
    print("Subscribing to topic '{}'...".format(message_topic))
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=message_topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received)

    subscribe_result = subscribe_future.result()
    print("Subscribed with {}".format(str(subscribe_result['qos'])))

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