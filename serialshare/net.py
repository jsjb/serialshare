""" networking and i/o """
import asyncio

import websockets

class NetSerial(asyncio.Protocol):
    def __init__(self, serial_device, websocket):
        self.device = serial_device
        self.ws = websocket
