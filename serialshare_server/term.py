"""
A module for handling terminal input/output for serialshare-server
"""

import asyncio
import atexit
import signal
import time

import asciimatics.screen
import asciimatics.event

import pyte.modes
import pyte.screens
import pyte.streams

from . import keycodes

# status lines
_STATUSES = [
    "Starting up...",
    "Waiting for host connection",
    "Connected.",
    "Shutting down...",
]


class Terminal:
    """
    a terminal-based terminal emulator that reads data to display and writes
    received input to/from a pipe
    """
    def __init__(self, pipe, fps=60):
        self.pipe = pipe
        self.fps = fps

        # status index
        self.status = 0

        # catch ctrl-c so we can send it across the websocket
        self.ctrlc = asyncio.Event()
        self.ctrlc.clear()

        # create asciimatics Screen interface to user's real terminal
        self.screen = asciimatics.screen.Screen.open()
        # draw the status line separator
        self.screen.centre('--------------------', self.screen.height - 2)
        # render the almost blank screen
        self.screen.refresh()

        # create pyte in-memory terminal
        # the pyte screen draws terminal commands onto a virtual screen, stored
        # as a buffer of characters
        self.termscreen = pyte.screens.HistoryScreen(
            self.screen.width,
            self.screen.height - 2,
            15000
        )
        # the pyte stream parses bytes and turns them into terminal commands
        # for the screen to draw
        self.termstream = pyte.streams.ByteStream(
            screen=self.termscreen,
            strict=False
        )
        # clear the screen
        self.termscreen.reset()
        # store the current cursor position for rendering later
        self.last_cursor = self.termscreen.cursor

        atexit.register(self.cleanup)

    def cleanup(self):
        """ closes self.screen, maybe other things later """
        self.screen.clear()
        self.screen.refresh()
        self.screen.close()
        atexit.unregister(self.cleanup)

    def sig_handler(self, signum, frame):
        """ signal handler. should only be set to catch ctrl-c """
        del frame  # resolves pylint w0163

        if signum == signal.SIGINT:
            self.ctrlc.set()

    def __await__(self):
        return self.termloop().__await__()

    async def termloop(self):
        """ create & gather tasks, and run them with the appropriate pipes """
        async with self.pipe.open() as (from_ws, to_ws):
            if self.status < 1:
                self.status = 1

            asyncio.create_task(self.receive_bytes(from_ws))

            # run up to self.fps times per second
            while True:
                await asyncio.gather(
                    self.update_screen(),
                    self.send_input(to_ws)
                )
                await asyncio.sleep(1000 / self.fps / 100)

    async def receive_bytes(self, reader):
        """ takes bytes from reader and feeds them to termstream """
        while not reader.at_eof():
            data = await reader.read(16)
            if self.status < 2:
                self.status = 2

            self.termstream.feed(data)

    async def update_screen(self):
        """
        to be run once per frame.
        redraws terminal lines if necessary
        updates the cursor location every time
        draws the status line every time
        """

        self.screen.print_at(
            self.termscreen.display[self.last_cursor.y],
            0, self.last_cursor.y
        )

        # unhighlight old cursor location
        self.screen.highlight(
            self.last_cursor.x, self.last_cursor.y,
            1, 1,
            self.screen.COLOUR_GREEN, self.screen.COLOUR_BLUE
        )

        # redraw all lines that have changed
        for dirty in self.termscreen.dirty:
            self.screen.print_at(self.termscreen.display[dirty], 0, dirty)
        self.termscreen.dirty.clear()

        # highlight new cursor location
        self.screen.highlight(
            self.termscreen.cursor.x, self.termscreen.cursor.y,
            1, 1,
            self.screen.COLOUR_BLACK, self.screen.COLOUR_WHITE
        )

        # store new cursor location
        self.last_cursor = self.termscreen.cursor

        # clear status line
        self.screen.centre(
            '\t'.expandtabs(self.screen.width),
            self.screen.height - 1
        )

        current_time = time.ctime()
        self.screen.print_at(
            current_time,
            self.screen.width - len(current_time),
            self.screen.height - 1
        )

        # draw status line
        self.screen.centre(_STATUSES[self.status], self.screen.height - 1)

        # render screen to user's real terminal
        self.screen.refresh()

    async def send_input(self, writer):
        """
        captures input from user's real terminal and sends it to `writer`
        """
        if self.ctrlc.is_set():
            self.ctrlc.clear()

            # if a connection hasn't been made yet, ctrl-c closes the program
            if self.status < 2:
                raise KeyboardInterrupt

            event = asciimatics.event.KeyboardEvent(self.screen.ctrl('c'))
        else:
            event = self.screen.get_event()

        while event is not None:
            if isinstance(event, asciimatics.event.KeyboardEvent):
                # get the byte sequence for the key(s) pressed
                code = keycodes.lookup(event.key_code)

                # send it
                if self.status >= 2:
                    await writer.drain()
                    writer.write(code)

            # skip waiting if there's another keypress to read
            event = self.screen.get_event()
