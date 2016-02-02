#!/usr/bin/env python

from distutils.core import setup
import nightcaste

setup(name='Nightcaste',
            version=nightcaste.__version__,
            description='A 2D Console-based Roguelike game.',
            author='Nicas Heydorn & Christofer Ostwald',
            author_email='murmox@gmail.com',
            url='https://github.com/murmox/nightcaste/',
            install_requires=[
                'cffi==1.5.0',
                'colorama==0.3.6',
                'libtcod-cffi==0.2.7',
                'py==1.4.31',
                'pycparser==2.14',
                'wheel==0.26.0',
            ],
            packages=['nightcaste'],
            platforms='any'
           )
