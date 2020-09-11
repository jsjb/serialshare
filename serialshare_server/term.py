"""
A module for handling terminal input/output for serialshare-server
"""

import asyncio
import atexit
import signal
import time
import queue

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


class Screen:
    """
    a wrapper for connecting a pyte Screen with an asciimatics Screen
    """
    def __init__(self):
        self.real = asciimatics.screen.Screen.open()
        self.virt = pyte.screens.HistoryScreen(
            self.real.width,
            self.real.height - 2,
            15000
        )

        # draw the status line separator
        self.real.centre('--------------------', self.real.height - 2)
        # render the almost blank screen
        self.real.refresh()

        # clear the screen
        self.virt.reset()

        # the pyte stream parses bytes and turns them into terminal commands
        # for the screen to draw
        self.stream = pyte.streams.ByteStream(
            screen=self.virt,
            strict=False
        )

        # store the current cursor position for rendering later
        self.cursor = {
            "x": self.virt.cursor.x,
            "y": self.virt.cursor.y,
        }

    def cleanup(self):
        """ clears, resets, and closes all displays components """
        self.real.clear()
        self.virt.reset()
        self.real.refresh()
        self.real.close()

    async def update(self, status):
        """
        to be run once per frame.
        redraws terminal lines if necessary
        updates the cursor location every time
        draws the status line every time
        """

        self.real.print_at(
            self.virt.display[self.cursor["y"]],
            0, self.cursor["y"]
        )

        # unhighlight old cursor location
        self.real.highlight(
            self.cursor["x"], self.cursor["y"],
            1, 1,
            self.real.COLOUR_WHITE, self.real.COLOUR_BLACK
        )

        # redraw all lines that have changed
        for dirty in self.virt.dirty:
            self.real.print_at(
                self.virt.display[dirty], 0,
                dirty
            )
        self.virt.dirty.clear()

        # highlight new cursor location
        self.real.highlight(
            self.virt.cursor.x, self.virt.cursor.y,
            1, 1,
            self.real.COLOUR_BLACK, self.real.COLOUR_WHITE
        )

        # store new cursor location
        self.cursor["x"] = self.virt.cursor.x
        self.cursor["y"] = self.virt.cursor.y

        # clear status line
        self.real.centre(
            '\t'.expandtabs(self.real.width),
            self.real.height - 1
        )

        current_time = time.ctime()
        self.real.print_at(
            current_time,
            self.real.width - len(current_time),
            self.real.height - 1
        )

        # draw status line
        self.real.centre(
            status,
            self.real.height - 1
        )

        # render screen to user's real terminal
        self.real.refresh()


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

        # queue for knowing when to return from await self
        self.quitqueue = asyncio.Queue()

        self.screen = Screen()

        atexit.register(self.cleanup)

    def cleanup(self):
        """ closes self.screen, maybe other things later """
        self.screen.cleanup()
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

            outputqueue = queue.Queue()
            loop = asyncio.get_running_loop()

            asyncio.create_task(self.receive_bytes(from_ws, outputqueue))
            loop.run_in_executor(
                None,
                _feed_bytes,
                outputqueue,
                self.screen.stream
            )

            # run up to self.fps times per second
            while self.quitqueue.empty():
                await asyncio.gather(
                    self.screen.update(_STATUSES[self.status]),
                    self.send_input(to_ws)
                )
                await asyncio.sleep(1000 / self.fps / 1000)

            return self.quitqueue.get_nowait()

    async def receive_bytes(self, reader, q):
        """ takes bytes from reader and feeds them to the queue.Queue """
        while not reader.at_eof():
            if self.status < 2:
                self.status = 2
            data = await reader.read(128)
            q.put(data)


    async def send_input(self, writer):
        """
        captures input from user's real terminal and sends it to `writer`
        """
        if self.ctrlc.is_set():
            self.ctrlc.clear()

            # if a connection hasn't been made yet, ctrl-c closes the program
            if self.status < 2:
                # just raise an exception if we've already tried graceful quit
                if self.quitqueue.qsize() > 0:
                    raise KeyboardInterrupt

                # otherwise, by all means, quit as gracefully as we can
                await self.quitqueue.put("ctrl-c")

            event = asciimatics.event.KeyboardEvent(self.screen.real.ctrl('c'))
        else:
            event = self.screen.real.get_event()

        while event is not None:
            if isinstance(event, asciimatics.event.KeyboardEvent):
                # get the byte sequence for the key(s) pressed
                code = keycodes.lookup(event.key_code)

                # send it
                if self.status >= 2:
                    try:
                        await writer.drain()
                    except ConnectionResetError as reset_error:
                        await self.quitqueue.put(
                            "connection error: " + str(reset_error)
                        )
                    writer.write(code)

            # skip waiting if there's another keypress to read
            event = self.screen.real.get_event()


def _feed_bytes(q, feedable):
    """
    accepts a queue.Queue and continuously reads it into feedable
    """
    while True:
        feedable.feed(q.get(block=True, timeout=None))

