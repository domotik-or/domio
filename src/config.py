import logging
from pathlib import Path

import tomli

from src.typem import DoorbellConfig
from src.typem import GeneralConfig
from src.typem import I2cConfig
from src.typem import LinkyConfig
from src.typem import LoggerConfig
from src.typem import MqttConfig
from src.typem import UpsConfig

doorbell = None
general = None
i2c = None
linky = None
loggers = {}
mqtt = None
ups = None

_module = []


def read(config_filename: str):
    config_file = Path(config_filename)
    with open(config_file, "rb") as f:
        raw_config = tomli.load(f)

    global doorbell
    doorbell = DoorbellConfig(**raw_config["doorbell"])

    global general
    general = GeneralConfig(**raw_config["general"])

    global i2c
    i2c = I2cConfig(**raw_config["i2c"])

    global linky
    linky = LinkyConfig(**raw_config["linky"])

    global loggers
    for lg in raw_config["logger"]:
        level_str = raw_config["logger"][lg]["level"]
        level = getattr(logging, level_str)
        loggers[lg] = LoggerConfig(level)

    global mqtt
    mqtt = MqttConfig(**raw_config["mqtt"])

    global ups
    ups = UpsConfig(**raw_config["ups"])
