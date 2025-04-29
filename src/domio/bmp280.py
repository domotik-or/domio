# inspired from
# https://github.com/feyzikesim/bmp280/blob/master/bmp_280/bmp_280.py

# This copy is different from the original : Modified by Franck Barbenoire
# (fbarbenoire@gmail.com)

import asyncio
from functools import partial
import logging

from smbus2 import SMBus

import domio.config as config
import domio.i2c as i2c
from domio.utils import done_callback

# BMP280 default address.
BMP280_I2C_ADDR = 0x77

# Operating Modes
SLEEP_MODE = 0
FORCED_MODE = 1
NORMAL_MODE = 3

DIG_T1 = 0x88
DIG_T2 = 0x8A
DIG_T3 = 0x8C

DIG_P1 = 0x8E
DIG_P2 = 0x90
DIG_P3 = 0x92
DIG_P4 = 0x94
DIG_P5 = 0x96
DIG_P6 = 0x98
DIG_P7 = 0x9A
DIG_P8 = 0x9C
DIG_P9 = 0x9E

# Registers
DEVICE_ID = 0xD0
RESET = 0xE0
STATUS = 0xF3
CTRL_MEAS = 0xF4
CONFIG = 0xF5
PRESSURE = 0xF7
TEMPERATURE = 0xFA

# Commands
RESET_CMD = 0xB6

OVERSAMPLING_P_NONE = 0b000
OVERSAMPLING_P_x1   = 0b001
OVERSAMPLING_P_x2   = 0b010
OVERSAMPLING_P_x4   = 0b011
OVERSAMPLING_P_x8   = 0b100
OVERSAMPLING_P_x16  = 0b101

OVERSAMPLING_T_NONE = 0b000
OVERSAMPLING_T_x1   = 0b001
OVERSAMPLING_T_x2   = 0b010
OVERSAMPLING_T_x4   = 0b011
OVERSAMPLING_T_x8   = 0b100
OVERSAMPLING_T_x16  = 0b101

T_STANDBY_0p5 = 0b000
T_STANDBY_62p5 = 0b001
T_STANDBY_125 = 0b010
T_STANDBY_250 = 0b011
T_STANDBY_500 = 0b100
T_STANDBY_1000 = 0b101
T_STANDBY_2000 = 0b110
T_STANDBY_4000 = 0b111

IIR_FILTER_OFF = 0b000
IIR_FILTER_x2  = 0b001
IIR_FILTER_x4  = 0b010
IIR_FILTER_x8  = 0b011
IIR_FILTER_x16 = 0b100

_altitude = 0.0
_bmp280 = None
_pressure = 0.0
_running = True
_task = None
_temperature = 0.0

# logger initial setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def twos_complement(input):
    if input > 32767:
        return input - 65536
    else:
        return input


def swap_bytes(v: int) -> int:
    return ((v & 0xff) << 8) + ((v >> 8) & 0xff)


class Bmp280:

    def __init__(
        self, i2c: SMBus, mode=FORCED_MODE, oversampling_p=OVERSAMPLING_P_x16,
        oversampling_t=OVERSAMPLING_T_x1,
        filter=IIR_FILTER_OFF, standby=T_STANDBY_4000
    ):
        # Check that mode is valid.
        assert mode in [SLEEP_MODE, FORCED_MODE, NORMAL_MODE]
        self.__mode = mode
        self.__i2c = i2c

        self.t_fine = 0

        self.bmp280_init(mode, oversampling_p, oversampling_t, filter, standby)

    def read_device_id(self):
        return self.__i2c.read_byte_data(BMP280_I2C_ADDR, DEVICE_ID)

    def device_reset(self):
        self.bus.write_byte_data(self.BMP280_ADDR, self.RESET, self.RESET_CMD)
        sleep(1)

    def bmp280_init(self, mode, oversampling_p, oversampling_t, filter, standby):
        ctrl_meas_reg = mode + (oversampling_p << 2) + (oversampling_t << 5)
        self.__i2c.write_byte_data(BMP280_I2C_ADDR, CTRL_MEAS, ctrl_meas_reg)

        config_reg = 0b000 + (filter << 2) + (standby << 5)
        self.__i2c.write_byte_data(BMP280_I2C_ADDR, CONFIG, config_reg)

    def read_temperature(self) -> float:
        t1 = self.__i2c.read_word_data(BMP280_I2C_ADDR, DIG_T1)
        t2 = twos_complement(self.__i2c.read_word_data(BMP280_I2C_ADDR, DIG_T2))
        t3 = twos_complement(self.__i2c.read_word_data(BMP280_I2C_ADDR, DIG_T3))

        raw_data = self.__i2c.read_i2c_block_data(BMP280_I2C_ADDR, TEMPERATURE, 3)
        adc_t = (raw_data[0] * pow(2, 16) + raw_data[1] * pow(2, 8) + raw_data[2]) >> 4

        var1 = ((adc_t / 16384.0) - (t1 / 1024.0)) * t2
        var2 = ((adc_t / 131072.0) - (t1 / 8192.0)) * (((adc_t / 131072.0) - (t1 / 8192.0)) * t3)
        self.t_fine = var1 + var2
        return (var1 + var2) / 5120.0

    def read_pressure(self) -> float:
        p1 = self.__i2c.read_word_data(BMP280_I2C_ADDR, DIG_P1)
        p2 = twos_complement(self.__i2c.read_word_data(BMP280_I2C_ADDR, DIG_P2))
        p3 = twos_complement(self.__i2c.read_word_data(BMP280_I2C_ADDR, DIG_P3))
        p4 = twos_complement(self.__i2c.read_word_data(BMP280_I2C_ADDR, DIG_P4))
        p5 = twos_complement(self.__i2c.read_word_data(BMP280_I2C_ADDR, DIG_P5))
        p6 = twos_complement(self.__i2c.read_word_data(BMP280_I2C_ADDR, DIG_P6))
        p7 = twos_complement(self.__i2c.read_word_data(BMP280_I2C_ADDR, DIG_P7))
        p8 = twos_complement(self.__i2c.read_word_data(BMP280_I2C_ADDR, DIG_P8))
        p9 = twos_complement(self.__i2c.read_word_data(BMP280_I2C_ADDR, DIG_P9))

        raw_data = self.__i2c.read_i2c_block_data(BMP280_I2C_ADDR, PRESSURE, 3)
        adc_p = (raw_data[0] * pow(2, 16) + raw_data[1] * pow(2, 8) + raw_data[2]) >> 4

        self.read_temperature()

        var1 = (self.t_fine / 2.0) - 64000.0
        var2 = var1 * var1 * p6 / 32768.0
        var2 += var1 * p5 * 2.0
        var2 = (var2 / 4.0) + (p4 * 65536.0)
        var1 = (p3 * var1 * var1 / 524288.0 + (p2 * var1)) / 524288.0
        var1 = (1.0 + (var1 / 32768.0)) * p1
        p = 1048576.0 - adc_p
        p = (p - (var2 / 4096.0)) * 6250.0 / var1
        var1 = p9 * p * p / 2147483648.0
        var2 = p * p8 / 32768.0
        p += (var1 + var2 + p7) / 16.0
        logger.debug(f"Pressure: {p} Pa")
        return p

    async def read_altitude(self, sealevel_pa=101325.0) -> float:
        """Calculates the altitude in meters."""
        # Calculation taken straight from section 3.6 of the datasheet.
        pressure = float(self.read_pressure())
        altitude = 44330.0 * (1.0 - pow(pressure / sealevel_pa, (1.0 / 5.255)))
        logger.debug(f"Altitude: {altitude} m")
        return altitude


def init(bus: SMBus, altitude: float):
    global _altitude
    global _bmp280
    global _task

    _altitude = altitude
    _bmp280 = Bmp280(bus, mode=NORMAL_MODE)

    if _task is None:
        _task = asyncio.create_task(_bmp280_task())
        _task.add_done_callback(partial(done_callback, logger))


async def close():
    global _running
    global _task

    _running = False
    if _task is not None:
        try:
            await _task
        except Exception:
            # task exceptions are handled by the done callback
            pass
        _task = None


async def _bmp280_task():
    global _pressure
    global _running
    global _temperature

    _running = True
    while _running:
        _pressure = _bmp280.read_pressure()
        _temperature = _bmp280.read_temperature()
        logger.debug(f"temperature: {_temperature}°C, pressure: {_pressure:f} Pa")
        await asyncio.sleep(5)


def get_pressure() -> float:
    return _pressure


def get_sea_level_pressure() -> float:
    return _pressure / pow(1.0 - _altitude / 44330.0, 5.255)


def get_temperature() -> float:
    return _temperature


async def run(config_filename: str):
    config.read(config_filename)

    init(config.i2c.bus)

    # pressure = await _bmp280.read_pressure()
    pressure = _bmp280.read_pressure()
    temperature = _bmp280.read_temperature()

    logger.debug(f"temperature: {temperature}°C, pressure: {pressure} Pa")


# main is used for test purpose as standalone
if __name__ == "__main__":
    import argparse
    import sys

    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter("%(asctime)s %(module)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.toml")
    args = parser.parse_args()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run(args.config))
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(close())
        loop.stop()
        logger.info("done")
