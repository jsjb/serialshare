"""
functions for communicating with serial devices
"""

import serial
import serial.tools.list_ports


# for serial device reads
DEFAULT_TIMEOUT = 1


def list_devices():
    """ return a dict of device names, keyed by description """
    return {str(d): d.device for d in serial.tools.list_ports.comports()}


def open_port(port, baudrate):
    """ return a serial port object """
    return serial.Serial(port, baudrate, timeout=DEFAULT_TIMEOUT)
