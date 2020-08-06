"""
A module for handling terminal input/output for serialshare-server
"""

import asyncio
import atexit
import signal

import asciimatics.screen
import asciimatics.event

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
        signal.signal(signal.SIGINT, self._sig_handler)

        # create asciimatics Screen interface to user's real terminal
        self.screen = asciimatics.screen.Screen.open()
        self.screen.centre('--------------------', self.screen.height - 2)
        self.screen.refresh()

        # create pyte in-memory terminal
        self.termscreen = pyte.screens.HistoryScreen(
            self.screen.width,
            self.screen.height - 2,
            15000
        )
        self.termstream = pyte.streams.ByteStream(
            screen=self.termscreen,
            strict=False
        )
        self.termscreen.reset()

        atexit.register(self._cleanup)

    def _cleanup(self):
        """ closes self.screen, maybe other things later """
        self.screen.clear()
        self.screen.refresh()
        self.screen.close()

    def _sig_handler(self, signum, frame):
        if signum == signal.SIGINT:
            self.ctrlc.set()

    def __await__(self):
        return self.termloop().__await__()

    async def termloop(self):
        """ create & gather tasks, and run them with the appropriate pipes """
        async with self.pipe.open() as (from_ws, to_ws):
            # TODO: find a better place to set status = 2
            if self.status < 2:
                self.status = 2

            asyncio.create_task(self.receive_bytes(from_ws))

            # run almost self.fps times per second
            while await asyncio.sleep(1000 / self.fps / 100):
                await asyncio.gather(
                    self.update_screen(),
                    self.send_input(to_ws)
                )


    async def receive_bytes(self, reader):
        """ takes bytes from reader and feeds them to termstream """
        byte = await reader.read(1)
        if self.status < 2:
            self.status = 2
        while not reader.at_eof():
            self.termstream.feed(byte)


    async def update_screen(self):
        """
        to be run once per frame.
        redraws the screen if necessary
        updates the cursor location every time
        draws the status line every time
        """
        cursor = self.termscreen.cursor
        # unhighlight old cursor location
        self.screen.highlight(
            cursor.x, cursor.y,
            1, 1,
            self.screen.COLOUR_WHITE, self.screen.COLOUR_BLACK
        )

        # redraw all lines that have changed
        for dirty in self.termscreen.dirty:
            self.screen.print_at(self.termscreen.display[dirty], 0, dirty)
        self.termscreen.dirty.clear()

        # highlight current cursor location
        self.screen.highlight(
            cursor.x, cursor.y,
            1, 1,
            self.screen.COLOUR_BLACK, self.screen.COLOUR_WHITE
        )

        # clear status line
        self.screen.centre(
            '\t'.expandtabs(self.screen.width),
            self.screen.height - 1
        )

        # draw status line
        self.screen.centre(_STATUSES[self.status], self.screen.height - 1)

        # render screen to user's real terminal
        self.screen.refresh()

    async def send_input(self, writer):
        """
        captures input from user's real terminal and sends it to the websocket
        """
        if self.ctrlc.is_set():
            self.ctrlc.clear()

            # if a connection hasn't been made yet, ctrl-c closes the program
            if self.status < 2:
                # TODO: write this
                pass

            event = asciimatics.event.KeyboardEvent(self.screen.ctrl('c'))
        else:
            event = self.screen.get_event()

        while event is not None:
            if isinstance(event, asciimatics.event.KeyboardEvent):
                # get the ascii value
                code = keycodes.lookup(event.key_code)

                # send it
                if self.status >= 2:
                    writer.write(code)

            # skip waiting if there's another keypress to read
            event = self.screen.get_event()
