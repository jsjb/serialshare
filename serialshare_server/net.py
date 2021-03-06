"""
A module for handling the network component of serialshare-server
"""

import asyncio
import http
import os
import sys

import websockets

_MESSAGE_SERIAL = 0
_MESSAGE_SYNC = 1


async def process_request(path, headers):
    """ if the index is requested, display a webpage """
    del headers  # revolves pylint w0163

    if path == "/":
        dir_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        index_file = os.path.join(dir_path, 'index.html')

        # prepare for the worst :)
        status = http.HTTPStatus.INTERNAL_SERVER_ERROR
        headers = []
        body = f"500 - couldn't read {index_file}.\n".encode('utf-8')

        try:
            with open(index_file, 'rb') as index:
                status = http.HTTPStatus.OK
                headers = [('Content-Type', 'text/html')]
                body = index.read()
        except FileNotFoundError:
            status = http.HTTPStatus.NOT_FOUND
            body = b"404 - couldn't find index.html"
        finally:
            return status, headers, body

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
                # send some garbage data ending in 0x01 to signal a connection
                to_term.write(b'\x00\x01')
                await to_term.drain()

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
            elif mtype == _MESSAGE_SYNC:
                # TODO: implement file sync
                pass
