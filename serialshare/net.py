""" networking and i/o """
import asyncio

import websockets

class WebSerial(asyncio.Protocol):
    """ represents serial port linked with websocket """
    def __init__(self, serial_device, websocket):
        self.device = serial_device
        self.ws = websocket


