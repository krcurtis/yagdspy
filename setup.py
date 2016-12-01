
# from distutils.core import setup

from setuptools import setup, find_packages


# or use find_packages()   from setuptools ??



packages = find_packages();

print packages

setup(name='yagdspy',
      author='Keith Curtis',
      description='Graph dependancy system for processing tasks',
      license='To be determined, for Hutch internal use at moment',
      version='1.0',
      packages=packages
      )
