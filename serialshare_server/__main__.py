#!/usr/bin/env python
"""
Server component for serialshare.
Accepts a websocket connection and links it to the local terminal
"""

import asyncio

import aiopipe

from . import net
from . import term


# duplex pipe for communication between network i/o task and terminal i/o task
net_pipe, term_pipe = aiopipe.aioduplex()

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.gather(
    term.Terminal(term_pipe, fps=60),
    net.Server(net_pipe, host="0.0.0.0", port=8080),
))
loop.run_forever()

print('connection lost.')
