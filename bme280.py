from ctypes import c_short, c_byte, c_ubyte

from bmp280 import BMP280, BMP280Error


BME280Error = BMP280Error


class BME280(BMP280):
    """Library for BME280 humidity, pressure & temperature sensor."""

    # Registers
    CALIBRATION_H1 = 0xa1
    CALIBRATION_HX = 0xe1  # - 0xe7 (H2-H6, different types => 7 bytes)

    CTRL_HUM = 0xf2  # read/write - write active after CTRL_MEAS write

    HUM = 0xfd  # - 0xfe (msb, lsb)

    def __init__(self, bus=None, alternativeAddress=False):
        """Create object representing BME280 chip."""
        super().__init__(bus, alternativeAddress)

    def calibrate(self):
        """Calibrate using data stored in device."""
        super().calibrate()
        dataH1 = self._bus.read_i2c_block_data(self.addr,
                                               self.CALIBRATION_H1, 1)
        dataHX = self._bus.read_i2c_block_data(self.addr,
                                               self.CALIBRATION_HX, 7)

        self.dig_H1 = float(c_ubyte(dataH1[0]).value)
        self.dig_H2 = float(c_short((dataHX[1] << 8) + dataHX[0]).value)
        self.dig_H3 = float(c_ubyte(dataHX[2]).value)
        self.dig_H4 = float(c_short(
            (dataHX[3] << 4) + (dataHX[4] & 0xf)).value)
        self.dig_H5 = float(c_short(
            (dataHX[5] << 4) + ((dataHX[4] & 0xf0) >> 4)).value)
        self.dig_H6 = float(c_byte(dataHX[6]).value)

    @property
    def id(self):
        """Return chip ID - should be 96 (0x60)."""
        return super().id()

    @property
    def ctrl_hum(self):
        """Return (raw) value of ctrl_hum register."""
        return self._bus.read_byte_data(self.addr, self.CTRL_HUM)

    def _ctrl_hum_set(self, osrs_h):
        """Set ctrl_hum register (for internal use)."""
        data = osrs_h & 0x7
        self._bus.write_byte_data(self.addr, self.CTRL_HUM,
                                  data)

    def set_acquisition_options(self, temperature_oversampling,
                                pressure_oversampling, mode,
                                humidity_oversampling=None):
        """Set acquisition options."""
        if humidity_oversampling is not None:
            ho = humidity_oversampling
            if ho == 0:
                osrs_h = self.OVERSAMPLING_SKIPPED
            elif ho == 1:
                osrs_h = self.OVERSAMPLING_1X
            elif ho == 2:
                osrs_h = self.OVERSAMPLING_2X
            elif ho == 4:
                osrs_h = self.OVERSAMPLING_4X
            elif ho == 8:
                osrs_h = self.OVERSAMPLING_8X
            elif ho == 16:
                osrs_h = self.OVERSAMPLING_16X
            else:
                raise BME280Error('Unsupported humidity oversampling')

            self._ctrl_hum_set(osrs_h)

        super().set_acquisition_options(
            temperature_oversampling, pressure_oversampling, mode)

    def set_config(self, inactive_time=0, filter_constant=0, spi_3wire=None):
        """Set configuration options."""
        it = inactive_time
        if (it == 0) or (it == 1):
            t_sb = self.STANDBY_1_MS
        elif it == 63:
            t_sb = self.STANDBY_63_MS
        elif it == 125:
            t_sb = self.STANDBY_125_MS
        elif it == 250:
            t_sb = self.STANDBY_250_MS
        elif it == 500:
            t_sb = self.STANDBY_500_MS
        elif it == 1000:
            t_sb = self.STANDBY_1000_MS
        elif it == 2000:
            raise BME280Error('Inactive time 2000ms not supported on BME280')
        elif it == 4000:
            raise BME280Error('Inactive time 4000ms not supported on BME280')
        elif it == 10:
            t_sb = self.STANDBY_2000_MS
        elif it == 20:
            t_sb = self.STANDBY_4000_MS
        else:
            raise BME280Error('Unsupported inactive time')

        self._set_config_internal(t_sb, inactive_time,
                                  filter_constant, spi_3wire)

    def raw_humidity(self):
        """Return measured humidity (raw data)."""
        data = self._bus.read_i2c_block_data(self.addr, self.HUM, 2)
        return (data[0] << 8) + data[1]

    def humidity(self, update_temperature=True):
        """Return measured humidity in %RH."""
        if (self.t_fine is None) or update_temperature:
            self.temperature()

        adc_H = float(self.raw_humidity())
        var_H = self.t_fine - 76800.0
        var_H = (
            (adc_H - (self.dig_H4 * 64.0 + self.dig_H5 / 16384.0 * var_H)) *
            (self.dig_H2 / 65536.0 * (
                1.0 + self.dig_H6 / 67108864.0 * var_H *
                (1.0 + self.dig_H3 / 67108864.0 * var_H)))
        )
        var_H = var_H * (1.0 - self.dig_H1 * var_H / 524288.0)

        if (var_H > 100.0):
            var_H = 100.0
        elif (var_H < 0.0):
            var_H = 0.0

        return round(var_H, 3)
