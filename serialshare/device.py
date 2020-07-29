"""
functions for communicating with serial devices
"""

import serial
import serial.tools.list_ports


def list_devices():
    """ return a dict of device names, keyed by description """
    return {str(d): d.device for d in serial.tools.list_ports.comports()}

def open_port(port):
    return serial.Serial(port)
