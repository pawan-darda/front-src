# -*- coding: latin-1 -*-
import sys
from setuptools import setup, find_packages

requires = []

setup(name='FrontUtils',
      version="1.4.7",
      author='CI team',
      description = 'Provides miscellenaous services for Front CI services',
      packages = find_packages(),
      install_requires = requires)
