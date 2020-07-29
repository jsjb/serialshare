#!/usr/bin/env python3
"""
A program for connecting a local serial port to serialshare-server

Whan started, this program asks for the following information by GUI:
    * server URL (textbox)
    * serial port (dropdown)
Upon answer, it connects to a serialshare-server instance and enables
communication between the given serial port and the server.
"""

from . import device
from . import ui
import websockets


options = {
    "device": None,
    "display": None,
}

devices = device.list_devices()
ui.inputwindow(options, devices.keys())

print(devices[options["device"]])
