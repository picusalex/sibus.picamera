#!/usr/bin/env python
# -*- coding: utf-8 -*-
import signal
import socket
import sys
import time

import picamera

from sibus_lib import BusElement, sibus_init, MessageObject

SERVICE_NAME = "sibus.picamera"
logger, cfg_data = sibus_init(SERVICE_NAME)


def start_camera():
    logger.info("Starting piCamera")
    camera = picamera.PiCamera()
    # camera.resolution = (640, 480)
    camera.framerate = 24

    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', 8000))
    server_socket.listen(0)

    message = MessageObject(data={
        "url": "8000"
    }, topic="info.camera.connected")
    busclient.publish(message)

    # Accept a single connection and make a file-like object out of it
    connection = server_socket.accept()[0].makefile('wb')
    try:
        camera.start_recording(connection, format='h264')
        camera.wait_recording(60)
        camera.stop_recording()
    finally:
        connection.close()
        server_socket.close()

    message = MessageObject(data={
        "url": "8000"
    }, topic="info.camera.disconnected")
    busclient.publish(message)


busclient = BusElement(SERVICE_NAME)
busclient.start()


def sigterm_handler(_signo=None, _stack_frame=None):
    busclient.stop()
    logger.info("Program terminated correctly")
    sys.exit(0)


signal.signal(signal.SIGTERM, sigterm_handler)

try:
    while 1:
        start_camera()
        time.sleep(5)
except KeyboardInterrupt:
    logger.info("Ctrl+C detected !")
except Exception as e:
    busclient.stop()
    logger.exception("Program terminated incorrectly ! " + str(e))
    sys.exit(1)
finally:
    sigterm_handler()
