#!/usr/bin/env python
"""
Server component for serialshare.
Accepts a websocket connection and links it to the local terminal
"""

import asyncio
import multiprocessing
import signal

import aiopipe

from . import net
from . import term


async def net_server(pipe):
    """ wrapper function for starting a net.Server connected to `pipe` """
    server = await net.Server(pipe, host="0.0.0.0", port=8080)
    return await server.wait_closed()


def net_proc(pipe):
    """ wrapper for running net_server on its own thread/process """
    asyncio.run(net_server(pipe))


async def main():
    """ wait for both terminal and websocket handlers to run """

    # duplex pipe for communication between network and terminal i/o tasks
    net_pipe, term_pipe = aiopipe.aioduplex()

    # network process
    with net_pipe.detach() as net_pipe:
        proc = multiprocessing.Process(target=net_proc, args=(net_pipe,))
        proc.start()

    terminal = term.Terminal(term_pipe, fps=60)

    # catch ctrl-c and send it to the terminal task
    signal.signal(signal.SIGINT, terminal.sig_handler)

    # reason for the terminal process exiting
    reason = None

    try:
        reason = await terminal
        terminal.cleanup()
    except KeyboardInterrupt:
        reason = 'caught unprocessed ctrl-c multiple times'
        terminal.cleanup()
    finally:
        print(reason if not None else 'closed terminal?')

        # restore the default handler for the ctrl-c event
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        proc.terminate()

# disable general catching of ctrl-c
signal.signal(signal.SIGINT, signal.SIG_IGN)

asyncio.run(main())

print('connection lost.')
