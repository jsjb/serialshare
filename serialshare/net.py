""" networking and i/o """
import asyncio

import websockets.client


class WebSerial(asyncio.Protocol):
    """ represents serial port linked with websocket """
    def __init__(self, websocket, loop):
        self.websocket = websocket
        self.loop = loop
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        print('serial port opened')
        # Ctrl-C, Ctrl-D, Ctrl-C, newline
        # this should reboot a CircuitPython device and open the REPL
        transport.write(b'\x03\x04\x03\n')

    def data_received(self, data):
        # TODO: remove this print once the server works
        print("got data", data)
        return asyncio.create_task(self.websocket.send(data))

    def connection_lost(self, exc):
        self.transport.loop.stop()


async def connect(host):
    """ returns a websocket connection """
    return websockets.client.connect("ws://{}".format(host))
