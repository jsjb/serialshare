#!/usr/bin/env python
"""
Server component for serialshare.
Accepts a websocket connection and links it to the local terminal
"""

import asyncio
import signal
import sys
import os

from . import keycodes

import asciimatics
import asciimatics.screen
import asciimatics.event

import websockets


ctrlc = asyncio.Event()
ctrlc.clear()


def handler(signum, frame):
    global ctrlc
    ctrlc.set()

signal.signal(signal.SIGINT, handler)

screen = asciimatics.screen.Screen.open()
screen.refresh()


async def get_messages(websocket):
    cursor_x = 0
    cursor_y = 0
    try:
        async for message in websocket:
            lastbyte = 0x00
            for byte in message:
                # word wrap
                if cursor_x >= screen.width:
                    cursor_x = 0
                    cursor_y += 1
                # TODO: scroll
                if cursor_y >= screen.height - 2:
                    cursor_y = 0

                if byte == ord('\n'):
                    # crlf
                    if lastbyte in (ord('\r'), ord('\n')):
                        cursor_y += 1
                        cursor_x = 0
                        for x in range(cursor_x, screen.width):
                            screen.print_at(' ', x, cursor_y)
                    else:
                        cursor_y += 1
                elif lastbyte == ord('\r'):
                    # carriage return
                    cursor_x = 0
                elif byte == ord('\t'):
                    if cursor_x % 0 != 0:
                        cursor_x += 1

                    while cursor_x % 8 != 0:
                        screen.print_at(' ', cursor_x, cursor_y)
                        cursor_x += 1
                elif byte == ord('\b'):
                    # backspace
                    cursor_x -= 1
                    screen.print_at(' ', cursor_x, cursor_y)
                else:
                    # hopefully a printable character or terminal control char
                    screen.print_at(chr(byte), cursor_x, cursor_y)
                    cursor_x += 1

                lastbyte = byte

            screen.refresh()
    except websockets.exceptions.ConnectionClosedError:
        return

async def send_input(websocket, loop):
    global ctrlc
    if ctrlc.is_set():
        ctrlc.clear()
        ev = asciimatics.event.KeyboardEvent(screen.ctrl('c'))
    else:
        ev = screen.get_event()
    while ev is not None:
        if isinstance(ev, asciimatics.event.KeyboardEvent):
            # get the ascii value
            code = keycodes.lookup(ev.key_code)

            # apply network encoding
            try:
                enc = code.to_bytes(1, 'big', signed=True)
            except OverflowError:
                enc = code.to_bytes(2, 'big', signed=True)

            # print for debugging purposes
            screen.print_at('                ', 0, screen.height - 1)
            screen.print_at(str(enc), 0, screen.height - 1)

            # send it
            await websocket.send(enc)
            # skip waiting if there's another keypress to read
            ev = screen.get_event()

    loop.create_task(send_input(websocket, loop))


async def consume(websocket, path):
    asyncio.get_running_loop().create_task(send_input(websocket, loop))
    await get_messages(websocket)
    await asyncio.sleep(3)
    asyncio.get_running_loop().stop()

start_server = websockets.serve(consume, "localhost", 8089)

loop = asyncio.get_event_loop()
loop.run_until_complete(start_server)
loop.run_forever()

screen.clear()
screen.refresh()
screen.close()
print('connection lost.')
