from pathlib import Path
from datetime import timedelta
import tomllib
from types import SimpleNamespace

from gpiod.line import Bias
from gpiod.line import Direction
from gpiod.line import Edge
from gpiod.line import Drive
from gpiod.line import Value

from domio.typem import CanConfig
from domio.typem import GeneralConfig
from domio.typem import GpioConfig
from domio.typem import I2cConfig
from domio.typem import LinkyConfig
from domio.typem import MqttConfig

can = None
general = None
gpios = SimpleNamespace()
i2c = None
linky = None
loggers = {}
mqtt = None


def read(config_filename: str):
    config_file = Path(config_filename).expanduser()

    with open(config_file, "rb") as f:
        raw_config = tomllib.load(f)

    global can
    can = CanConfig(**raw_config["can"])

    global general
    general = GeneralConfig(**raw_config["general"])

    global gpios  # noqa
    for k, v in raw_config["gpio"].items():
        #  direction attribute is mandatory
        v["direction"] = getattr(Direction, v["direction"].upper())

        if "debounce_period" in v:
            # value in µs
            v["debounce_period"] = timedelta(seconds=v["debounce_period"] / 1000000)

        if "bias" in v:
            v["bias"] = getattr(Bias, v["bias"].upper())

        if "drive" in v:
            v["drive"] = getattr(Drive, v["drive"].upper())

        if "edge_detection" in v:
            v["edge_detection"] = getattr(Edge, v["edge_detection"].upper())

        if "output_value" in v:
            v["output_value"] = getattr(Value, v["output_value"].upper())

        setattr(gpios, k, GpioConfig(**v))

    global i2c
    i2c = I2cConfig(**raw_config["i2c"])

    global linky
    linky = LinkyConfig(**raw_config["linky"])

    global loggers
    loggers = raw_config["logger"]

    global mqtt
    mqtt = MqttConfig(**raw_config["mqtt"])
