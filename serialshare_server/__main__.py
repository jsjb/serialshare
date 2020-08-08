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
    """
    start a websocket server that writes to and reads from `pipe`, then wait
    for it to close
    """
    srvr = await net.Server(pipe, host="0.0.0.0", port=8080)
    return await srvr.wait_closed()


def net_proc(pipe):
    """ simple wrapper function for net_server """
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

    await terminal

    terminal.cleanup()
    print('closed terminal')

    # enable the default handler for the ctrl-c event
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    return proc.terminate()

# disable general catching of ctrl-c
signal.signal(signal.SIGINT, signal.SIG_IGN)

asyncio.run(main())

print('connection lost.')
