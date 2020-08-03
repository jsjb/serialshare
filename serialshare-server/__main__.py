#!/usr/bin/env python
"""
Server component for serialshare.
Accepts a websocket connection and links it to the local terminal
"""

import asyncio
import os
import signal
import sys
import types

from . import keycodes

import asciimatics
import asciimatics.screen
import asciimatics.event

import pyte.streams
import pyte.screens

import websockets


STATUSES = [
    "Starting up...",
    "Waiting for host connection",
    "Connected.",
    "Shutting down...",
]

global_state = types.SimpleNamespace(
    fps=15,
    status=0,
    websocket=None
)

ctrlc = asyncio.Event()
ctrlc.clear()


def handler(signum, frame):
    global ctrlc
    if signum == signal.SIGINT:
        ctrlc.set()

signal.signal(signal.SIGINT, handler)

screen = asciimatics.screen.Screen.open()
screen.centre('--------------------', screen.height - 2)
screen.refresh()

termscreen = pyte.screens.HistoryScreen(screen.width, screen.height - 2, 15000)
termstream = pyte.streams.ByteStream(screen=termscreen, strict=False)
termscreen.reset()


async def get_messages(websocket):
    try:
        async for message in websocket:
            mtype = message[0]
            message = message[1:]
            if mtype == 0:
                termstream.feed(message)

    except websockets.exceptions.ConnectionClosedError:
        return


async def update_screen(state):
    # clear highlights
    screen.highlight(
        0, 0,
        screen.height, screen.width,
        screen.COLOUR_WHITE, screen.COLOUR_BLACK
    )

    # draw lines
    for dirty in termscreen.dirty:
        screen.print_at(termscreen.display[dirty], 0, dirty)
    termscreen.dirty.clear()

    # highlight cursor location
    cursor = termscreen.cursor
    screen.highlight(
        cursor.x, cursor.y,
        1, 1,
        screen.COLOUR_BLACK, screen.COLOUR_WHITE
    )

    # clear status line
    screen.centre('\t'.expandtabs(screen.width), screen.height - 1)
    # draw status
    screen.centre(STATUSES[state.status], screen.height - 1)

    # draw
    screen.refresh()

    # fire almost `fps` times per second
    await asyncio.sleep(1000 / state.fps / 1000)
    if state.websocket is None or state.websocket.open:
        asyncio.get_running_loop().create_task(update_screen(state))


async def send_input(state):
    global ctrlc
    if ctrlc.is_set():
        ctrlc.clear()

        # if a connection hasn't been made yet, ctrl-c closes the program
        if state.websocket is None or state.websocket.open == False:
            asyncio.get_running_loop().stop()
            return

        ev = asciimatics.event.KeyboardEvent(screen.ctrl('c'))
    else:
        ev = screen.get_event()

    while ev is not None:
        if isinstance(ev, asciimatics.event.KeyboardEvent):
            # get the ascii value
            code = keycodes.lookup(ev.key_code)

            # print for debugging purposes
            screen.print_at('          ', screen.width - 10, screen.height - 1)
            screen.print_at(str(code), screen.width - 10, screen.height - 1)
            screen.print_at('                ', 0, screen.height - 1)
            screen.print_at(str(code), 0, screen.height - 1)

            # send it
            if state.websocket is not None:
                await state.websocket.send(b'\x00' + code)
            # skip waiting if there's another keypress to read
            ev = screen.get_event()

    # fire almost (`fps` / 10) times per second
    await asyncio.sleep(1000 / state.fps / 100)
    if state.websocket.open:
        asyncio.get_running_loop().create_task(send_input(state))


async def consume(websocket, path):
    global_state.status = 2
    global_state.websocket = websocket
    evloop = asyncio.get_running_loop()
    try:
        evloop.create_task(send_input(global_state))
        await get_messages(websocket)
    except e:
        print("connection lost !!!!!", e)
    await asyncio.sleep(3)
    asyncio.get_running_loop().stop()

start_server = websockets.serve(consume, "localhost", 8089)

loop = asyncio.get_event_loop()
loop.create_task(update_screen(global_state))
global_state.status = 1
loop.run_until_complete(start_server)
loop.run_forever()

screen.clear()
screen.refresh()
screen.close()
print('connection lost.')
