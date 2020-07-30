"""
functions for communicating with serial devices
"""

import asyncio

import serial_asyncio
import serial.tools.list_ports


# for serial device reads
DEFAULT_TIMEOUT = 1


def list_devices():
    """ return a dict of device names, keyed by description """
    return {str(d): d.device for d in serial.tools.list_ports.comports()}


def open_port(device, baudrate):
    """ return a serial port object """
    return serial.Serial(device, baudrate, timeout=DEFAULT_TIMEOUT)
