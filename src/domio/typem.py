from dataclasses import dataclass
from datetime import timedelta
# from enum import auto
# from enum import Enum
# from enum import IntEnum
from typing import Optional

from gpiod.line import Bias
from gpiod.line import Direction
from gpiod.line import Drive
from gpiod.line import Edge
from gpiod.line import Value


@dataclass
class CanConfig:
    channel: str
    interface: str


class DomioException(Exception):
    pass


@dataclass
class GpioConfig:
    direction: Direction
    gpio_num: int
    active_low: Optional[bool] = None
    bias: Optional[Bias] = None
    debounce_period: Optional[timedelta] = None
    drive: Optional[Drive] = None
    edge_detection: Optional[Edge] = None
    output_value: Optional[Value] = None


@dataclass
class GeneralConfig:
    altitude: float
    gpio_device: str
    port: int


@dataclass
class I2cConfig:
    bus: int


@dataclass
class LinkyConfig:
    serial_port: int
    baudrate: int
    bytesize: str
    stopbits: str
    parity: str


@dataclass
class MqttConfig:
    hostname: str
    port: int
