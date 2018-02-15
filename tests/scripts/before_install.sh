#!/usr/bin/env bash
# -*- mode: sh; -*-

# File: before_install.sh
# Time-stamp: <2018-02-15 13:30:08>
# Copyright (C) 2018 Sergei Antipov
# Description:

# set -o xtrace
set -o nounset
set -o errexit
set -o pipefail

sudo apt-get update
# Latest Ansible install
sudo apt-add-repository -y ppa:ansible/ansible
sudo apt-get update
sudo apt-get install ansible python-pip -y
python --version
ansible --version
docker version
sudo pip install docker-py
# Pull docker image or build it
if [ -f tests/Dockerfile.${DISTRIBUTION}_${DIST_VERSION} ]
then
    sudo docker build --rm=true --file=tests/Dockerfile.${DISTRIBUTION}_${DIST_VERSION}
    --tag ${DISTRIBUTION}:${DIST_VERSION} tests
else
    sudo docker pull ${DISTRIBUTION}:${DIST_VERSION}
fi

sudo ln -s ${PWD} /etc/ansible/roles/greendayonfire.mongodb
