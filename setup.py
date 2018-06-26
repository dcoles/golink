# Copyright 2018 David Coles <coles.david@gmail.com>
# This project is licensed under the terms of the MIT license. See LICENSE.txt
from setuptools import setup

setup(
    name='golink',
    version='0.0.1',
    packages=['golink'],
    url='https://github.com/dcoles/golink',
    license='MIT',
    author='dcoles',
    author_email='coles.david@gmail.com',
    description='A server for creating customized HTTP redirects.',
    package_data={
        'golink.templates': ['*.html'],
    },
)
