#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="theonix-core",
    version="1.0.0",
    description="Theonix OS Shared Platform Foundation & Core Services",
    author="The Theonix Team",
    packages=find_packages(),
    install_requires=[
        "PyQt6",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
    ],
)
