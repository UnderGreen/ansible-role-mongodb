FROM debian:8

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    apt install --yes python-minimal && \
    rm /lib/systemd/system/getty@.service
