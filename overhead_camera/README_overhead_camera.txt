This folder contains the code for setting up and operating the overhead camera from the base station system. 

calibration/ - holds file unfisheye_video.py used calibrate the overhead camera. Since a fisheye lens camera was used for our demo and a un-fisheye version would be needed for implementing concepts found in the visionary implementation, a rough calibration set up was implemented. Resulting coefficients are stored in calibration_mapx, calibration_mapy, calibration_roi, to be used by streaming file. Before and after image results stored in rawresult.png and calibresult.png. Other calibration attempts and coefficients based on different resolutions can be found in folder other_attempts_tests/. 

The calibration set up was done with reference to the tutorial at https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_calib3d/py_calibration/py_calibration.html 


MQTT related files copied over from repo provided by another member, please refer to main directory for latest files. Files include: 
gps.pyGroundSystem-PolicyGroundSystem.cert.pemGroundSystem.private.keyGroundSystem.public.keyJetson-PolicyJetson.cert.pemJetson.private.keyJetson.public.keypub.pypubsub.py
sub.pyutils

Required functions from sub.py were copied over to stream files listed below for better integration
Citation for MQTT Files:
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.

To stream:

1) stream_save_track.py: takes input camera stream, reroutes it to a virtual camera to stream through Jitsi Meet, records and locally saves frames to recordings of each test session (controlled by start and stop of each test from UI). 


2) stream_save_track_unwarped.py: takes input camera stream, un-fisheyes frames, reroutes them to a virtual camera to stream through Jitsi Meet, records and locally saves frames to recordings of each test session (controlled by start and stop of each test from UI). 

3) stream_save_track_unwarped2.py: Attempt at an improved stream quality of 2) by un-fisheyeing a higher quality stream, includes commented out attempt of automatically joining Jitsi Meet meeting (unfinished)

To run:
sudo modprobe v4l2loopback devices=1

python3 pub.py --endpoint aicgt013q5xy-ats.iot.us-east-1.amazonaws.com --ca_file root-CA.crt --cert GroundSystem.cert.pem  --key GroundSystem.private.key --client_id groundSysGps --topic groundsys/video --count 0

For 1)
python3 stream_save_track.py --key GroundSystem.private.key --cert GroundSystem.cert.pem --client_id groundSysVideo --topic groundsys/video --endpoint aicgt013q5xy-ats.iot.us-east-1.amazonaws.com --ca_file root-CA.crt --count 0

Or For 2) 
python3 stream_save_track_unwarped.py --key GroundSystem.private.key --cert GroundSystem.cert.pem --client_id groundSysVideo --topic groundsys/video --endpoint aicgt013q5xy-ats.iot.us-east-1.amazonaws.com --ca_file root-CA.crt --count 0

Open Jitsi Meet Meeting and connect to "Dummy Webcam" (virtual camera port)

Recordings are saved in recordings/streamX.mp4 where X is the test number. 

Referred to: https://github.com/letmaik/pyvirtualcam/blob/main/examples/video.py
For implementing the use of a virtual webcam

Referred to: https://www.geeksforgeeks.org/saving-operated-video-from-a-webcam-using-opencv/
For examples of how to save video streams using OpenCV. 
Example code referred to can be found in folder example_code/

Name: Vasudha Srinivasan, AndrewID: vasudhas, Date: 06/20/2023