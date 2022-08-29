# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in shared_finance_app/__init__.py
from shared_finance_app import __version__ as version

setup(
	name='shared_finance_app',
	version=version,
	description='Shared Finance App',
	author='mesa_Safd',
	author_email='meso1132',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
