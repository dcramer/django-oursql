#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='django-oursql',
    version='.'.join(map(str, __import__('mysql_oursql').__version__)),
    author='David Cramer',
    author_email='dcramer@gmail.com',
    url='http://github.com/dcramer/django-oursql',
    install_requires=[
        'Django>=1.0',
        'oursql',
    ],
    description = 'Django database backend for MySQL via oursql.',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)