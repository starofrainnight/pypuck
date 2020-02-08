#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import io
from setuptools import setup, find_packages

setup(
    name="helloworld",
    version="0.0.1",
    description="A project just demonstrate how to wrap a simple python app",
    packages=find_packages(),
    entry_points={"console_scripts": ["helloworld=helloworld.__main__:main"]},
    include_package_data=True,
    license="Apache Software License",
    zip_safe=False,
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
