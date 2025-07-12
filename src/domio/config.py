import logging
from pathlib import Path
import tomllib

from domio.typem import DoorbellConfig
from domio.typem import GeneralConfig
from domio.typem import I2cConfig
from domio.typem import LinkyConfig
from domio.typem import MqttConfig
from domio.typem import UpsConfig

doorbell = None
general = None
i2c = None
linky = None
loggers = {}
mqtt = None
network = None
ups = None


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

    global ups
    ups = UpsConfig(**raw_config["ups"])
