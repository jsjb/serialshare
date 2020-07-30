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
import asyncio

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

loop = asyncio.get_event_loop()


async def main():
    """ connects serial port with websocket """
    websocket = await net.connect(profile["hostname"])
    webserial = net.WebSerial(websocket, loop)

    transport, _ = await device.open_dev(
        loop,
        lambda: webserial,
        profile["device"],
        profile["baudrate"]
    )
    async for message in websocket:
        transport.write(bytes(message, encoding='utf-8'))

loop.run_until_complete(main())
loop.run_forever()
loop.close()
