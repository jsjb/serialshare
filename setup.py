#!/usr/bin/env python3
""" A setup script for serialshare """

from distutils.core import setup

setup(name='serialshare',
      version='1.0',
      packages=['serialshare', 'serialshare-server'],
      install_requires=[
          'pyserial==3.4',
          'pyserial-asyncio==0.4',
          'websockets==8.1'
      ]
      )
