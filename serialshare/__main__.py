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
from . import data

# fetch last used settings, or the defaults
profile = data.read_profile()
print(profile)

all_devices = device.list_devices()

# configure profile from gui
ui.inputwindow(profile, all_devices.keys())

# save profile
data.write_profile(profile)

# pull just the name of the device from the dict
profile["device"] = all_devices[profile["device"]]
# fix up baudrate from string
profile["baudrate"] = int(profile["baudrate"])

print("Connecting device {} at {} baud to host {}.".format(
    profile["device"], profile["baudrate"], profile["hostname"]
))

dev = options["device"]
baud = options["baudrate"]
local = device.open_port(dev, baud)
