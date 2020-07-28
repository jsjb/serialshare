#!/usr/bin/env python3
"""
Asks for the following information by GUI:
    * server URL (textbox)
    * serial port (dropdown)
Upon answer, connects to a serialshare-server instance and enables
communication between the given serial port and the server.
"""

import serial
import websockets
