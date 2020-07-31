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
ui.input_window(profile, all_devices.keys())

# save profile
data.write_profile(profile)

# pull just the name of the device from the dict
profile["device"] = all_devices[profile["device"]]
# fix up baudrate from string
profile["baudrate"] = int(profile["baudrate"])

print("Connecting device {} at {} baud to host {}.".format(
    profile["device"], profile["baudrate"], profile["hostname"]
))


async def main(event_loop):
    """ connects serial port with websocket """
    # get our connection
    websocket = await net.connect(profile["hostname"])
    # create the protocol object for pyserial to write to
    webserial = net.WebSerial(websocket, event_loop)

    # read from the serial device into the websocket
    transport, _ = await device.open_dev(
        loop,
        lambda: webserial,
        profile["device"],
        profile["baudrate"]
    )

    # read from the websocket into the serial device
    async for message in websocket:
        # message is bytes if we send it as such, so no need to decode
        lastbyte = 0x00
        for byte in message:
            # fix newlines
            if byte == ord('\n') and lastbyte != ord('\r'):
                transport.write(b'\r\n')
            else:
                transport.write(bytes([byte]))


loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))
loop.run_forever()
loop.close()
