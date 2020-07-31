"""
functions for communicating with serial devices
"""

import serial_asyncio
import serial.tools.list_ports


def list_devices():
    """ return a dict of device names, keyed by description """
    return {str(d): d.device for d in serial.tools.list_ports.comports()}


def open_dev(loop, protofac, device, baudrate):
    """ return a local serial port connection """
    return serial_asyncio.create_serial_connection(
        loop,
        protofac,
        device,
        baudrate
    )
