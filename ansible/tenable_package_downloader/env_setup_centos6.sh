#!/bin/bash -x
#Do not set -e here, as if the host has epel package installed already, it will generate an error and stop the following commands

yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm
yum -y --skip-broken update
yum -y install python34 wget
wget https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py
pip install -r requirements.txt
