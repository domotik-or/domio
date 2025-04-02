#!/usr/bin/env python3

from setuptools import setup


setup(
    name="python3-domotik",
    version="0.1.0",
    description="Read Linky serial data and more",
    author="Franck Barbenoire",
    author_email="fbarbenoire@gmail.com",
    url="https://github.com/franckinux/python3-domotik",
    packages=["domotik"],
    package_dir={"domotik": "src"},
    include_package_data=True,
    install_requires=[
        "aiohttp", "aiomqtt", "pyserial-asyncio", "tomli"
    ],
    entry_points={
        "console_scripts": ["domotik=domotik.main:main", ]
    },
    python_requires='>=3.10',
    zip_safe=False,
    license="MIT"
)

# http://python-packaging.readthedocs.io/en/latest/command-line-scripts.html
