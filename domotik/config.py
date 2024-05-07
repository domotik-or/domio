import logging
from pathlib import Path

import tomli

from domotik.typem import DoorbellConfig
from domotik.typem import LinkyConfig
from domotik.typem import LoggerConfig

doorbell = None
linky = None

loggers = {}


def read(config_filename: str):
    config_file = Path(config_filename)
    with open(config_file, "rb") as f:
        raw_config = tomli.load(f)

    global doorbell
    doorbell = DoorbellConfig(**raw_config["doorbell"])

    global linky
    linky = LinkyConfig(**raw_config["linky"])

    global loggers
    for lg in raw_config["logger"]:
        level_str = raw_config["logger"][lg]["level"]
        level = getattr(logging, level_str)
        loggers[lg] = LoggerConfig(level)
