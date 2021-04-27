#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup

setup(name='lockpick',
      version='1.0.2',
      description='Distributed locking using Zookeeper',
      long_description=open(os.path.join(os.path.dirname(__file__),
                                         'README.md')).read(),
      long_description_content_type='text/markdown',
      url='https://github.com/raags/lockpick',
      author='Raghu Udiyar',
      author_email='raghusiddarth@gmail.com',
      license='MIT',
      py_modules=['lockpick'],
      install_requires='kazoo>=2.5.0',
      entry_points={
          'console_scripts': [
              'lockpick = lockpick:cli'
          ]}
      )
