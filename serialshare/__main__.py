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

import websockets.exceptions

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
    for tries in range(0,3):
        print('try', tries)
        try:
            websocket = await net.connect(profile["hostname"])
        except OSError:
            ui.error("connection failed.")
            if tries < 2:
                print("connection failed. retrying...")
                await asyncio.sleep(5/3)
                continue
            # after three tries (five seconds), give up
            event_loop.stop()
            return
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
    try:
        async for message in websocket:
            # message is bytes if we send it as such, so no need to decode
            # we do need to parse message type though
            mtype = message[0]
            MESSAGE_SERIAL = 0 # data to/from serial device
            MESSAGE_PING = 1 # websocket keepalive
            MESSAGE_PONG = 2 # keepalive response

            message = message[1:]

            if mtype == MESSAGE_SERIAL:
                lastbyte = 0x00
                print('received from server:', str(message))
                for byte in message:
                    ## fix newlines
                    #if byte == ord('\n') and lastbyte != ord('\r'):
                    #    transport.write(b'\r\n')
                    #else:
                    if True: # TODO: that's silly
                        transport.write(bytes([byte]))
            elif mtype == MESSAGE_PING:
                # respond to ping
                websocket.send(bytes[2, 0])

    except websockets.exceptions.ConnectionClosedError:
        print("connection lost.")
        asyncio.get_running_loop().stop()


loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))
loop.run_forever()
loop.close()
ui.error("serialshare has exited.")
