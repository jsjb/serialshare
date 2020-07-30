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

#localdev = device.open_port(profile["device"], profile["baudrate"])

import websockets.client
import serial_asyncio
import asyncio

loop = asyncio.get_event_loop()
#class WebSerialProtocol(websockets.client.WebSocketClientProtocol):
    #pass

class WebSerial(asyncio.Protocol):
    def __init__(self, websocket, loop):
        self.websocket = websocket
        self.loop = loop
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        print('serial port opened', transport)
        transport.write(b'\x03\x04\x03\n')

    def data_received(self, data):
        print("got data", data)
        return asyncio.create_task(self.websocket.send(data))

    def connection_lost(self, exc):
        self.transport.loop.stop()

async def wsprotofac():
    ws = await websockets.client.connect("ws://" + profile["hostname"])

    transport, protocol = await serial_asyncio.create_serial_connection(
        loop,
        lambda: WebSerial(ws, loop),
        profile["device"],
        profile["baudrate"]
    )

    async for message in ws:
        transport.write(bytes(message, encoding='utf-8'))

loop.run_until_complete(wsprotofac())
loop.run_forever()
loop.close()
