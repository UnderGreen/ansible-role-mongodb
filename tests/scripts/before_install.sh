#!/usr/bin/env bash
# -*- mode: sh; -*-

# File: before_install.sh
# Time-stamp: <2018-07-12 18:05:37>
# Copyright (C) 2018 Sergei Antipov
# Description:

# set -o xtrace
set -o nounset
set -o errexit
set -o pipefail

apk add --no-cache \
  ca-certificates \
  openssh-client

[ ! -e /etc/nsswitch.conf ] && echo 'hosts: files dns' > /etc/nsswitch.conf

export DOCKER_CHANNEL=stable
export DOCKER_VERSION=19.03.12

set -eux; \
	\
# this "case" statement is generated via "update.sh"
	apkArch="$(apk --print-arch)"; \
	case "$apkArch" in \
# amd64
		x86_64) dockerArch='x86_64' ;; \
# arm32v6
		armhf) dockerArch='armel' ;; \
# arm32v7
		armv7) dockerArch='armhf' ;; \
# arm64v8
		aarch64) dockerArch='aarch64' ;; \
		*) echo >&2 "error: unsupported architecture ($apkArch)"; exit 1 ;;\
	esac; \
	\
	if ! wget -O docker.tgz "https://download.docker.com/linux/static/${DOCKER_CHANNEL}/${dockerArch}/docker-${DOCKER_VERSION}.tgz"; then \
		echo >&2 "error: failed to download 'docker-${DOCKER_VERSION}' from '${DOCKER_CHANNEL}' for '${dockerArch}'"; \
		exit 1; \
	fi; \
	\
	tar --extract \
		--file docker.tgz \
		--strip-components 1 \
		--directory /usr/local/bin/ \
	; \
	rm docker.tgz; \
	\
	dockerd --version; \
	docker --version

export DOCKER_TLS_CERTDIR=/certs
mkdir /certs /certs/client && chmod 1777 /certs /certs/client

apk --update add --virtual build-dependencies libffi-dev openssl-dev python-dev build-base \
  && pip install docker ansible mitogen \
  && apk del --no-network build-dependencies

cat << EOF > ansible.cfg
[defaults]
pipelining = True
strategy = mitogen_linear
strategy_plugins = /usr/local/lib/python2.7/site-packages/ansible_mitogen/plugins/strategy
EOF

# Pull docker image or build it
if [ -f tests/Dockerfile.${DISTRIBUTION}_${DIST_VERSION} ]
then
    docker build --rm=true --file=tests/Dockerfile.${DISTRIBUTION}_${DIST_VERSION} --tag ${DISTRIBUTION}:${DIST_VERSION} tests
else
    docker pull ${DISTRIBUTION}:${DIST_VERSION}
fi

ln -s ${PWD} tests/greendayonfire.mongodb

