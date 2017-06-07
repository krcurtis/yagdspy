# Copyright 2016 Fred Hutchinson Cancer Research Center
# from distutils.core import setup

from setuptools import setup, find_packages


# or use find_packages()   from setuptools ??



packages = find_packages(exclude=['tests']);


setup(name='yagdspy',
      author='Keith Curtis',
      description='Graph dependancy system for processing tasks',
      license='GNU LGPLv3',
      version='1.0',
      packages=packages
      )
