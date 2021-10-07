#!/bin/bash
echo "Downloading the repository..."
echo

pwd=$(pwd)

# This part checks if the repo folder is already available
if [ -d $pwd"/OceanOptics-OPCUA" ]
then
    echo "Folder already exists!"
else
    git clone https://github.com/GiuseppeCogoni/OceanOptics-OPCUA.git
fi

# Changing directory to the downloaded repo
cd $pwd"/OceanOptics-OPCUA"

echo "Checking if ocean_ua:latest image already exist..."

# Verification if the docker image is already present
docker image inspect ocean_ua:latest >/dev/null 2>&1 && im="yes" || im="no"

if [ $im == "no" ]
then
    echo "Creating docker image..."
    docker build -t ocean_ua .
else
    echo "Docker image already available!"
fi


