"""
A module for handling terminal input/output for serialshare-server
"""

import asyncio
import atexit
import signal
import time
import threading
import queue

import asciimatics.screen
import asciimatics.event

import pyte.modes
import pyte.screens
import pyte.streams

from . import keycodes


class Screen:
    """
    a wrapper for connecting a pyte Screen with an asciimatics Screen
    """
    def __init__(self):
        self.real = asciimatics.screen.Screen.open()
        self.virt = pyte.screens.HistoryScreen(
            self.real.width,
            self.real.height - 2,
            150
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

    def drawloop(self, status, fps=60):
        """
        loops up to fps times per second
        redraws terminal lines if necessary
        updates the cursor location every frame
        draws the status line every frame
        """

        while status.get() < 3:
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
            # we work off a copy of the dirty line set so it doesn't change in
            # another thread while we're reading it, which would cause an error
            for dirty in self.virt.dirty.copy():
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
                status.string(),
                self.real.height - 1
            )

            # render screen to user's real terminal
            self.real.refresh()

            # only fire up to fps times per second
            time.sleep(1000 / fps / 1000)


class _Status:
    """
    a class shared by Terminal and Screen to pass a status line back and forth
    this is broken out into its own class for easier thread safety
    the atomicity of assignment is implementation dependent, so we lock a lot
    """
    _status_strings = [
        "Starting up...",
        "Waiting for host connection",
        "Connected.",
        "Shutting down...",
    ]

    def __init__(self, value=0):
        self.lock = threading.Lock()
        self.set(value)

    def set(self, value):
        """ sets the value of raw and updates string """
        self.lock.acquire(True)
        self.raw = value
        self.raw_string = _Status._status_strings[value]
        self.lock.release()

    def get(self):
        """ returns the value of raw """
        self.lock.acquire(True)
        ret = self.raw
        self.lock.release()
        return ret

    def string(self):
        """ returns a string describing the current status """
        self.lock.acquire(True)
        ret = self.raw_string
        self.lock.release()
        return ret


class Terminal:
    """
    a terminal-based terminal emulator that reads data to display and writes
    received input to/from a pipe
    """
    def __init__(self, pipe, fps=60):
        self.pipe = pipe
        self.fps = fps

        # status index
        self.status = _Status()

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
            if self.status.get() < 1:
                self.status.set(1)

            outputqueue = queue.Queue()
            loop = asyncio.get_running_loop()

            asyncio.create_task(self.receive_bytes(from_ws, outputqueue))
            loop.run_in_executor(
                None,
                _feed_bytes,
                self.status,
                outputqueue,
                self.screen.stream
            )

            loop.run_in_executor(
                None,
                self.screen.drawloop,
                self.status,
                self.fps
            )

            # run up to self.fps times per second
            while self.quitqueue.empty():
                await self.send_input(to_ws)
                await asyncio.sleep(1000 / self.fps / 1000)

            self.status.set(3)
            return self.quitqueue.get_nowait()


    async def receive_bytes(self, reader, screen_queue):
        """ takes bytes from reader and feeds them to the queue.Queue """
        first_run = 1
        while not reader.at_eof():
            if first_run == 1 and self.status.get() < 2:
                self.status.set(2)
            data = await reader.read(128)
            screen_queue.put(data)


    async def send_input(self, writer):
        """
        captures input from user's real terminal and sends it to `writer`
        """
        if self.ctrlc.is_set():
            self.ctrlc.clear()

            # if a connection hasn't been made yet, ctrl-c closes the program
            if self.status.get() < 2:
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
                if self.status.get() >= 2:
                    try:
                        await writer.drain()
                    except ConnectionResetError as reset_error:
                        await self.quitqueue.put(
                            "connection error: " + str(reset_error)
                        )
                    writer.write(code)

            # skip waiting if there's another keypress to read
            event = self.screen.real.get_event()


def _feed_bytes(status, screen_queue, feedable):
    """
    accepts a queue.Queue and continuously reads it into feedable
    """
    while status.get() < 3:
        feedable.feed(screen_queue.get(block=True, timeout=None))
