#!/usr/bin/env python3
""" A setup script for serialshare """

from distutils.core import setup

setup(name='serialshare',
      version='1.0',
      packages=['serialshare', 'serialshare-server'],
      install_requires=[
          'appdirs>1.4,<1.5',
          'asciimatics==1.11',
          'pyserial==3.4',
          'pyserial-asyncio==0.4',
          'pyte>=0.8.0,<=0.9'
          'websockets==8.1'
      ]
      )
