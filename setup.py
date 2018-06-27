#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(name='lockpick',
      version='0.1.0',
      description='Utility for distributed locking using Zookeeper',
      url='https://github.com/helpshift/lockpick',
      author='Raghu Udiyar',
      author_email='raghusiddarth@gmail.com',
      license='MIT',
      py_modules=['lockpick'],
      install_requires=['kazoo>=2.5.0',
                        'futures==3.2.0'],
      entry_points={
          'console_scripts': [
              'lockpick = lockpick:cli'
          ]}
      )
