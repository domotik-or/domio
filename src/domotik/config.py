import logging
from pathlib import Path
import tomllib

from domotik.typem import DoorbellConfig
from domotik.typem import GeneralConfig
from domotik.typem import I2cConfig
from domotik.typem import LinkyConfig
from domotik.typem import MqttConfig
from domotik.typem import NetworkConfig
from domotik.typem import UpsConfig

doorbell = None
general = None
i2c = None
linky = None
loggers = {}
mqtt = None
network = None
ups = None

_module = []


def read(config_filename: str):
    config_file = Path(config_filename).expanduser()

    with open(config_file, "rb") as f:
        raw_config = tomllib.load(f)

    global doorbell
    doorbell = DoorbellConfig(**raw_config["doorbell"])

    global general
    general = GeneralConfig(**raw_config["general"])

    global i2c
    i2c = I2cConfig(**raw_config["i2c"])

    global linky
    linky = LinkyConfig(**raw_config["linky"])

    global loggers
    loggers = raw_config["logger"]

    global mqtt
    mqtt = MqttConfig(**raw_config["mqtt"])

    global network
    network = NetworkConfig(**raw_config["network"])

    global ups
    ups = UpsConfig(**raw_config["ups"])
