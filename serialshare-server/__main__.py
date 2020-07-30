#!/usr/bin/env python

import asyncio
import websockets

async def get_messages(websocket):
    print('listening for messages')
    async for message in websocket:
        print(bytes.decode(message, encoding='utf-8'))

async def send_input(websocket):
    print('getting input')
    val = ""
    while val != 'quit':
        val = input("")
        await websocket.send(val + "\n")

async def consume(websocket, path):
    await asyncio.wait([get_messages(websocket), send_input(websocket)])

start_server = websockets.serve(consume, "localhost", 8089)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
