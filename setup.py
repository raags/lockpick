#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup

setup(name='lockpick-hsft',
      version='0.1.1',
      description='Utility for distributed locking using Zookeeper',
      long_description=open(os.path.join(os.path.dirname(__file__),
                                         'README.md')).read(),
      long_description_content_type='text/markdown',
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
