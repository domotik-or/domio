# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# This copy is different from the original : Modified by Franck Barbenoire
# (fbarbenoire@gmail.com)

import argparse
import asyncio
import logging

from smbus2 import SMBus

import domotik.config as config
import domotik.i2c as i2c

# BMP180 default address.
BMP180_I2C_ADDR = 0x77

# Operating Modes
BMP180_ULTRALOWPOWER = 0
BMP180_STANDARD = 1
BMP180_HIGHRES = 2
BMP180_ULTRAHIGHRES = 3

# BMP180 Registers
BMP180_CAL_AC1 = 0xAA  # R   Calibration data (16 bits)
BMP180_CAL_AC2 = 0xAC  # R   Calibration data (16 bits)
BMP180_CAL_AC3 = 0xAE  # R   Calibration data (16 bits)
BMP180_CAL_AC4 = 0xB0  # R   Calibration data (16 bits)
BMP180_CAL_AC5 = 0xB2  # R   Calibration data (16 bits)
BMP180_CAL_AC6 = 0xB4  # R   Calibration data (16 bits)
BMP180_CAL_B1 = 0xB6   # R   Calibration data (16 bits)
BMP180_CAL_B2 = 0xB8   # R   Calibration data (16 bits)
BMP180_CAL_MB = 0xBA   # R   Calibration data (16 bits)
BMP180_CAL_MC = 0xBC   # R   Calibration data (16 bits)
BMP180_CAL_MD = 0xBE   # R   Calibration data (16 bits)
BMP180_CONTROL = 0xF4
BMP180_TEMPDATA = 0xF6
BMP180_PRESSUREDATA = 0xF6

# Commands
BMP180_READTEMPCMD = 0x2E
BMP180_READPRESSURECMD = 0x34

_altitude = 0.0
_bmp180 = None
_pressure = 0.0
_running = True
_task = None
_temperature = 0.0

logger = logging.getLogger(__name__)


def twos_complement(input):
    if input > 32767:
        return input - 65536
    else:
        return input


def swap_bytes(v: int) -> int:
    return ((v & 0xff) << 8) + ((v >> 8) & 0xff)


class Bmp180:

    def __init__(self, i2c: SMBus, mode=BMP180_STANDARD):
        # Check that mode is valid.
        assert mode in [
            BMP180_ULTRALOWPOWER, BMP180_STANDARD,
            BMP180_HIGHRES, BMP180_ULTRAHIGHRES
        ]
        self.__mode = mode
        self.__i2c = i2c
        # Load calibration values.
        self.__load_calibration()
        # self.__load_datasheet_calibration()

        logger.debug(f"AC1: {self.__cal_AC1:6d}")
        logger.debug(f"AC2: {self.__cal_AC2:6d}")
        logger.debug(f"AC3: {self.__cal_AC3:6d}")
        logger.debug(f"AC4: {self.__cal_AC4:6d}")
        logger.debug(f"AC5: {self.__cal_AC5:6d}")
        logger.debug(f"AC6: {self.__cal_AC6:6d}")
        logger.debug(f"B1: {self.__cal_B1:6d}")
        logger.debug(f"B2: {self.__cal_B2:6d}")
        logger.debug(f"MB: {self.__cal_MB:6d}")
        logger.debug(f"MC: {self.__cal_MC:6d}")
        logger.debug(f"MD: {self.__cal_MD:6d}")

    def __load_calibration(self):
        # INT16
        self.__cal_AC1 = twos_complement(
            swap_bytes(
                self.__i2c.read_word_data(BMP180_I2C_ADDR, BMP180_CAL_AC1)
            )
        )
        # INT16
        self.__cal_AC2 = twos_complement(
            swap_bytes(
                self.__i2c.read_word_data(BMP180_I2C_ADDR, BMP180_CAL_AC2)
            )
        )
        # INT16
        self.__cal_AC3 = twos_complement(
            swap_bytes(
                self.__i2c.read_word_data(BMP180_I2C_ADDR, BMP180_CAL_AC3)
            )
        )
        # UINT16
        self.__cal_AC4 = swap_bytes(
            self.__i2c.read_word_data(BMP180_I2C_ADDR, BMP180_CAL_AC4)
        )
        # UINT16
        self.__cal_AC5 = swap_bytes(
            self.__i2c.read_word_data(BMP180_I2C_ADDR, BMP180_CAL_AC5)
        )
        # UINT16
        self.__cal_AC6 = swap_bytes(
            self.__i2c.read_word_data(BMP180_I2C_ADDR, BMP180_CAL_AC6)
        )
        # INT16
        self.__cal_B1 = twos_complement(
            swap_bytes(
                self.__i2c.read_word_data(BMP180_I2C_ADDR, BMP180_CAL_B1)
            )
        )
        # INT16
        self.__cal_B2 = twos_complement(
            swap_bytes(
                self.__i2c.read_word_data(BMP180_I2C_ADDR, BMP180_CAL_B2)
            )
        )
        # INT16
        self.__cal_MB = twos_complement(
            swap_bytes(
                self.__i2c.read_word_data(BMP180_I2C_ADDR, BMP180_CAL_MB)
            )
        )
        # INT16
        self.__cal_MC = twos_complement(
            swap_bytes(
                self.__i2c.read_word_data(BMP180_I2C_ADDR, BMP180_CAL_MC)
            )
        )
        # INT16
        self.__cal_MD = twos_complement(
            swap_bytes(
                self.__i2c.read_word_data(BMP180_I2C_ADDR, BMP180_CAL_MD)
            )
        )

    def __load_datasheet_calibration(self):
        # Set calibration from values in the datasheet example. Useful for
        # debugging the temp and pressure calculation accuracy.
        self.__cal_AC1 = 408
        self.__cal_AC2 = -72
        self.__cal_AC3 = -14383
        self.__cal_AC4 = 32741
        self.__cal_AC5 = 32757
        self.__cal_AC6 = 23153
        self.__cal_B1 = 6190
        self.__cal_B2 = 4
        self.__cal_MB = -32767
        self.__cal_MC = -8711
        self.__cal_MD = 2868

    async def __read_raw_temp(self) -> int:
        """Reads the raw (uncompensated) temperature from the sensor."""
        self.__i2c.write_byte_data(BMP180_I2C_ADDR, BMP180_CONTROL, BMP180_READTEMPCMD)
        await asyncio.sleep(0.005)  # Wait 5ms
        raw = swap_bytes(self.__i2c.read_word_data(BMP180_I2C_ADDR, BMP180_TEMPDATA))
        logger.debug(f"Raw temp: 0x{raw & 0xFFFF:X} ({raw})")
        return raw

    async def __read_raw_pressure(self) -> int:
        """Reads the raw (uncompensated) pressure level from the sensor."""
        self.__i2c.write_byte_data(BMP180_I2C_ADDR, BMP180_CONTROL, BMP180_READPRESSURECMD + (self.__mode << 6))
        if self.__mode == BMP180_ULTRALOWPOWER:
            await asyncio.sleep(0.005)
        elif self.__mode == BMP180_HIGHRES:
            await asyncio.sleep(0.014)
        elif self.__mode == BMP180_ULTRAHIGHRES:
            await asyncio.sleep(0.026)
        else:
            await asyncio.sleep(0.008)
        msb = self.__i2c.read_byte_data(BMP180_I2C_ADDR, BMP180_PRESSUREDATA)
        lsb = self.__i2c.read_byte_data(BMP180_I2C_ADDR, BMP180_PRESSUREDATA + 1)
        xlsb = self.__i2c.read_byte_data(BMP180_I2C_ADDR, BMP180_PRESSUREDATA + 2)
        raw = ((msb << 16) + (lsb << 8) + xlsb) >> (8 - self.__mode)
        logger.debug(f"Raw pressure: 0x{raw & 0xFFFFFF:06X} ({raw})")
        return raw

    async def read_temperature(self) -> float:
        """Gets the compensated temperature in degrees celsius."""
        UT = await self.__read_raw_temp()
        # Datasheet value for debugging:
        # UT = 27898
        # Calculations below are taken straight from section 3.5 of the datasheet
        X1 = ((UT - self.__cal_AC6) * self.__cal_AC5) >> 15
        X2 = (self.__cal_MC << 11) // (X1 + self.__cal_MD)
        B5 = X1 + X2
        temp = ((B5 + 8) >> 4) / 10.0
        logger.debug(f"Calibrated temperature: {temp}°C")
        return temp

    async def read_pressure(self) -> float:
        """Gets the compensated pressure in Pascals."""
        UT = await self.__read_raw_temp()
        UP = await self.__read_raw_pressure()
        # Datasheet values for debugging:
        # UT = 27898
        # UP = 23843
        # Calculations below are taken straight from section 3.5 of the datasheet
        # Calculate true temperature coefficient B5.
        X1 = ((UT - self.__cal_AC6) * self.__cal_AC5) >> 15
        X2 = (self.__cal_MC << 11) // (X1 + self.__cal_MD)
        B5 = X1 + X2
        logger.debug(f"B5: {B5}")
        # Pressure Calculations
        B6 = B5 - 4000
        logger.debug(f"B6: {B6}")
        X1 = (self.__cal_B2 * (B6 * B6) >> 12) >> 11
        X2 = (self.__cal_AC2 * B6) >> 11
        X3 = X1 + X2
        B3 = (((self.__cal_AC1 * 4 + X3) << self.__mode) + 2) // 4
        logger.debug(f"B3: {B3}")
        X1 = (self.__cal_AC3 * B6) >> 13
        X2 = (self.__cal_B1 * ((B6 * B6) >> 12)) >> 16
        X3 = ((X1 + X2) + 2) >> 2
        B4 = (self.__cal_AC4 * (X3 + 32768)) >> 15
        logger.debug(f"B4: {B4}")
        B7 = (UP - B3) * (50000 >> self.__mode)
        logger.debug(f"B7: {B7}")
        if B7 < 0x80000000:
            p = (B7 * 2) // B4
        else:
            p = (B7 // B4) * 2
        X1 = (p >> 8) * (p >> 8)
        X1 = (X1 * 3038) >> 16
        X2 = (-7357 * p) >> 16
        p = p + ((X1 + X2 + 3791) >> 4)
        logger.debug(f"Pressure: {p} Pa")
        return p

    async def read_altitude(self, sealevel_pa=101325.0) -> float:
        """Calculates the altitude in meters."""
        # Calculation taken straight from section 3.6 of the datasheet.
        pressure = float(await self.read_pressure())
        altitude = 44330.0 * (1.0 - pow(pressure / sealevel_pa, (1.0 / 5.255)))
        logger.debug(f"Altitude: {altitude} m")
        return altitude


def init(altitude: float):
    global _altitude
    global _bmp180
    global _task

    i2c.open_bus(config.i2c.bus)

    _altitude = altitude
    _bmp180 = Bmp180(i2c.get_bus())

    if _task is None:
        _task = asyncio.create_task(__task())


async def close():
    global _running

    _running = False
    if _task is not None:
        await _task


async def __task():
    global _pressure
    global _running
    global _temperature

    _running = True
    while _running:
        _pressure = await _bmp180.read_pressure()
        _temperature = await _bmp180.read_temperature()
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

    # pressure = await _bmp180.read_pressure()
    pressure = await _bmp180.read_pressure()
    temperature = await _bmp180.read_temperature()

    print(f"temperature: {temperature}°C, pressure: {pressure} Pa")

    await close()


# main is used for test purpose as standalone
if __name__ == "__main__":
    import sys

    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter("%(asctime)s %(module)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.toml")
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run(args.config))
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(close())
        loop.stop()
