
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.
# Retrieved from the connection module in AWS IoT core's user page

#!/usr/bin/env bash
# stop script on error
set -e

# Check for python 3
if ! python3 --version &> /dev/null; then
  printf "\nERROR: python3 must be installed.\n"
  exit 1
fi

# Check to see if root CA file exists, download if not
if [ ! -f ./root-CA.crt ]; then
  printf "\nDownloading AWS IoT Root CA certificate from AWS...\n"
  curl https://www.amazontrust.com/repository/AmazonRootCA1.pem > root-CA.crt
fi

# Check to see if AWS Device SDK for Python is already installed, install if not
if ! python3 -c "import awsiot" &> /dev/null; then
  printf "\nInstalling AWS SDK...\n"
  python3 -m pip install ./aws-iot-device-sdk-python-v2
  result=$?
  if [ $result -ne 0 ]; then
    printf "\nERROR: Failed to install SDK.\n"
    exit $result
  fi
fi

# run pub/sub sample app using certificates downloaded in package
printf "\nRunning pub/sub sample application...\n"
#python3 sub.py --endpoint aicgt013q5xy-ats.iot.us-east-1.amazonaws.com --ca_file root-CA.crt --cert Jetson.cert.pem --key Jetson.private.key --client_id basestation --topic sensors/temp --count 0
python3 sub.py --endpoint aicgt013q5xy-ats.iot.us-east-1.amazonaws.com --ca_file root-CA.crt --cert GroundSystem.cert.pem --key GroundSystem.private.key --client_id groundSysGps --topic esp32/pub --count 0
