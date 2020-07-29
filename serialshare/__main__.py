#!/usr/bin/env python3
"""
A program for connecting a local serial port to serialshare-server

Whan started, this program asks for the following information by GUI:
    * server URL (textbox)
    * serial port identifier (dropdown)
    * serial port baudrate (textbox)
Upon answer, it connects to a serialshare-server instance and enables
communication between the given serial port and the server.
"""

from . import device
from . import ui
from . import net


options = {
    "device": None,
    "baudrate": 9600,
    "hostname": None,
}

all_devices = device.list_devices()

# set options from gui
ui.inputwindow(options, all_devices.keys())

# pull just the name of the device from the dict
options["device"] = all_devices[options["device"]]
# fix up baudrate from string
options["baudrate"] = int(options["baudrate"])

print("Connecting device {} at {} baud to host {}.".format(
    options["device"], options["baudrate"], options["hostname"]
))

dev = options["device"]
baud = options["baudrate"]
local = device.open_port(dev, baud)
