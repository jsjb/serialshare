""" networking and i/o """
import asyncio
import time

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
        transport.write(b'\x03')
        time.sleep(0.1)
        transport.write(b'\x04')
        time.sleep(0.1)
        transport.write(b'\x03')
        time.sleep(0.1)
        transport.write(b'\x0a')

    def data_received(self, data):
        print("got data", data)
        coro = self.websocket.send(b'\x00' + data)
        return asyncio.create_task(coro)

    def connection_lost(self, exc):
        self.transport.loop.stop()


def connect(host):
    """ returns a websocket connection """
    # TODO: use wss, once the server is ready for deployment
    return websockets.client.connect(
        "ws://{}/ws".format(host),
        ping_interval=2,
        ping_timeout=10
    )
