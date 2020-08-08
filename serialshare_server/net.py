"""
A module for handling the network component of serialshare-server
"""

import asyncio
import http
import os
import sys

import websockets

_MESSAGE_SERIAL = 0


async def process_request(path, headers):
    """ if the index is requested, display a webpage """
    del headers  # revolves pylint w0163

    if path == "/":
        dir_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        with open(os.path.join(dir_path, 'index.html')) as index:
            return http.HTTPStatus.OK, [], index.read()

    return None


class Server:
    """
    network handling class
    """
    def __init__(self, pipe, host="0.0.0.0", port=8080):
        self.pipe = pipe
        self.websocket = None
        self.host = host
        self.port = port

    def __await__(self):
        coro = websockets.serve(
            self.ws_handler,
            host=self.host,
            port=self.port,
            process_request=process_request
        )
        return coro.__await__()

    async def ws_handler(self, websocket, path):
        """
        process incoming data
        """
        del path  # revolves pylint w0163

        if self.websocket is not None:
            websocket.close()
            return

        self.websocket = websocket

        try:
            async with self.pipe.open() as (from_term, to_term):
                await asyncio.gather(
                    self._from_term_handler(from_term),
                    self._to_term_handler(to_term)
                )
        except websockets.exceptions.ConnectionClosedError:
            return

    async def _from_term_handler(self, reader):
        while not reader.at_eof():
            await self.websocket.send(b'\x00' + await reader.read(16))

    async def _to_term_handler(self, writer):
        async for message in self.websocket:
            mtype = message[0]
            if mtype == _MESSAGE_SERIAL:
                writer.write(message[1:])
                await writer.drain()
