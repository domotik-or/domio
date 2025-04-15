#!/usr/bin/env python3

from setuptools import setup


setup(
    name="domotik",
    version="0.1.0",
    description="Read Linky serial data and more",
    author="Franck Barbenoire",
    author_email="fbarbenoire@gmail.com",
    url="https://github.com/domotik-or/domotik",
    packages=["domotik"],
    package_dir={"domotik": "src"},
    include_package_data=True,
    install_requires=[
        "aiohttp", "aiomqtt", "pyserial-asyncio"
    ],
    entry_points={
        "console_scripts": ["domotik=src.main:main", ]
    },
    python_requires='>=3.11',
    zip_safe=False,
    license="MIT"
)

# http://python-packaging.readthedocs.io/en/latest/command-line-scripts.html
