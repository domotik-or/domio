from dataclasses import dataclass
# from enum import auto
# from enum import Enum
# from enum import IntEnum


@dataclass
class DoorbellConfig:
    bell_gpio: int
    button_gpio: int


@dataclass
class LinkyConfig:
    serial_port: str
    baudrate: int
    parity: str
    databits: int


@dataclass
class LoggerConfig:
    level: int
