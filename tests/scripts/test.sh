#!/usr/bin/env bash
# -*- mode: sh; -*-

# File: test.sh
# Time-stamp: <2018-02-26 16:04:24>
# Copyright (C) 2018 Sergei Antipov
# Description:

# set -o xtrace
set -o nounset
set -o errexit

# Test 1
echo "ansible-playbook -i tests/hosts tests/site.yml -e target=mongo1 -e mongodb_version=${MONGODB_VERSION} -e image_name=${DISTRIBUTION}:${DIST_VERSION}"
ansible-playbook -i tests/hosts tests/site.yml -e target=mongo1 -e mongodb_version=${MONGODB_VERSION} -e image_name=${DISTRIBUTION}:${DIST_VERSION}
# Idempotence test
ansible-playbook -i tests/hosts tests/site.yml -e target=mongo1 -e mongodb_version=${MONGODB_VERSION} -e image_name=${DISTRIBUTION}:${DIST_VERSION} | \
    grep -q 'changed=0.*failed=0' && \
    (echo 'Idempotence test: pass' && exit 0) || (echo 'Idempotence test: fail' && exit 1)
# Delete all containers
docker kill mongo{1,2,3} && docker rm mongo{1,2,3}

# Test 2
echo "ansible-playbook -i tests/hosts tests/site.yml -e target=mongo1 -e image_name=${DISTRIBUTION}:${DIST_VERSION} -e mongodb_version=${MONGODB_VERSION} -e mongodb_security_authorization='enabled'"
ansible-playbook -i tests/hosts tests/site.yml -e target=mongo1 -e image_name=${DISTRIBUTION}:${DIST_VERSION} -e mongodb_version=${MONGODB_VERSION} -e mongodb_security_authorization='enabled'
# Idempotence test
ansible-playbook -i tests/hosts tests/site.yml -e target=mongo1 -e image_name=${DISTRIBUTION}:${DIST_VERSION} -e mongodb_version=${MONGODB_VERSION} -e mongodb_security_authorization='enabled' \
    | grep -q 'changed=0.*failed=0' \
    && (echo 'Idempotence test: pass' && exit 0) || (echo 'Idempotence test: fail' && exit 1)
# Delete all containers
docker kill mongo{1,2,3} && docker rm mongo{1,2,3}

# Test 3
echo "ansible-playbook -i tests/hosts tests/site.yml -e target=mongo -e image_name=${DISTRIBUTION}:${DIST_VERSION} -e mongodb_version=${MONGODB_VERSION} -e mongodb_replication_replset='testrs'"
ansible-playbook -i tests/hosts tests/site.yml -e target=mongo -e image_name=${DISTRIBUTION}:${DIST_VERSION} -e mongodb_version=${MONGODB_VERSION} -e mongodb_replication_replset='testrs'
# Idempotence test
ansible-playbook -i tests/hosts tests/site.yml -e target=mongo -e image_name=${DISTRIBUTION}:${DIST_VERSION} -e mongodb_version=${MONGODB_VERSION} -e mongodb_replication_replset='testrs' \
    | grep -q 'changed=0.*failed=0' \
    && (echo 'Idempotence test: pass' && exit 0) || (echo 'Idempotence test: fail' && exit 1)
# Delete all containers
docker kill mongo{1,2,3} && docker rm mongo{1,2,3}

# Test 4
echo "ansible-playbook -i tests/hosts tests/site.yml -e target=mongo -e image_name=${DISTRIBUTION}:${DIST_VERSION} -e mongodb_version=${MONGODB_VERSION} -e mongodb_replication_replset='testrs' -e mongodb_security_authorization='enabled'"
ansible-playbook -i tests/hosts tests/site.yml -e target=mongo -e image_name=${DISTRIBUTION}:${DIST_VERSION} -e mongodb_version=${MONGODB_VERSION} -e mongodb_replication_replset='testrs' -e mongodb_security_authorization='enabled'
# Idempotence test
ansible-playbook -i tests/hosts tests/site.yml -e target=mongo -e image_name=${DISTRIBUTION}:${DIST_VERSION} -e mongodb_version=${MONGODB_VERSION} -e mongodb_replication_replset='testrs' -e mongodb_security_authorization='enabled' \
    | grep -q 'changed=0.*failed=0' \
    && (echo 'Idempotence test: pass' && exit 0) || (echo 'Idempotence test: fail' && exit 1)
