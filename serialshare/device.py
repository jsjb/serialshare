"""
functions for communicating with serial devices
"""

import serial.tools.list_ports


def list_devices():
    return {str(d): d.device for d in serial.tools.list_ports.comports()}
