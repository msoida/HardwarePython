from ctypes import c_short, c_ushort
from i2c import I2CBus, I2CError


class BMP280Error(I2CError):
    pass


class BMP280(object):
    """Library for BMP280 pressure & temperature sensor."""

    I2C_ADDRESS = 0x77
    I2C_ADDRESS2 = 0x76

    # Registers
    CALIBRATION = 0x88  # - 0x9f (T1-T3 and P1-P9, all 16-bit => 24 bytes)
    ID = 0xd0  # read only
    RESET = 0xe0  # write only
    STATUS = 0xf3  # read only
    CTRL_MEAS = 0xf4  # read/write
    CONFIG = 0xf5  # read/write
    PRESS = 0xf7  # - 0xf9 (msb, lsb, xlsb)
    TEMP = 0xfa  # - 0xfc (msb, lsb, xlsb)

    # Constants
    SLEEP_MODE = 0x00
    FORCED_MODE = 0x01
    NORMAL_MODE = 0x03

    SOFT_RESET = 0xb6

    STANDBY_1_MS = 0x00
    STANDBY_63_MS = 0x01
    STANDBY_125_MS = 0x02
    STANDBY_250_MS = 0x03
    STANDBY_500_MS = 0x04
    STANDBY_1000_MS = 0x05
    STANDBY_2000_MS = 0x06
    STANDBY_4000_MS = 0x07

    OVERSAMPLING_SKIPPED = 0x00
    OVERSAMPLING_1X = 0x01
    OVERSAMPLING_2X = 0x02
    OVERSAMPLING_4X = 0x03
    OVERSAMPLING_8X = 0x04
    OVERSAMPLING_16X = 0x05

    FILTER_OFF = 0x00
    FILTER_2 = 0x01
    FILTER_4 = 0x02
    FILTER_8 = 0x03
    FILTER_16 = 0x04

    def __init__(self, bus=None, alternativeAddress=False):
        """Create object representing BMP280 chip."""
        self._bus = I2CBus(bus)
        self.addr = self.I2C_ADDRESS
        if alternativeAddress:
            self.addr = self.I2C_ADDRESS2
        self.t_fine = None
        self.calibrate()

    def calibrate(self):
        """Calibrate using data stored in device."""
        data = self._bus.read_i2c_block_data(self.addr,
                                             self.CALIBRATION, 24)
        self.dig_T1 = float(c_ushort((data[1] << 8) + data[0]).value)
        self.dig_T2 = float(c_short((data[3] << 8) + data[2]).value)
        self.dig_T3 = float(c_short((data[5] << 8) + data[4]).value)
        self.dig_P1 = float(c_ushort((data[7] << 8) + data[6]).value)
        self.dig_P2 = float(c_short((data[9] << 8) + data[8]).value)
        self.dig_P3 = float(c_short((data[11] << 8) + data[10]).value)
        self.dig_P4 = float(c_short((data[13] << 8) + data[12]).value)
        self.dig_P5 = float(c_short((data[15] << 8) + data[14]).value)
        self.dig_P6 = float(c_short((data[17] << 8) + data[16]).value)
        self.dig_P7 = float(c_short((data[19] << 8) + data[18]).value)
        self.dig_P8 = float(c_short((data[21] << 8) + data[20]).value)
        self.dig_P9 = float(c_short((data[23] << 8) + data[22]).value)

    @property
    def id(self):
        """Return chip ID - should be 88 (0x58)."""
        return self._bus.read_byte_data(self.addr, self.ID)

    def reset(self):
        """Reset all internal registers."""
        self._bus.write_byte_data(self.addr, self.RESET,
                                  self.SOFT_RESET)

    @property
    def status(self):
        """Return current device status as tuple (measuring, im_update)."""
        data = self._bus.read_byte_data(self.addr, self.STATUS)
        measuring = bool((data >> 3) % 2)
        im_update = bool(data % 2)
        return (measuring, im_update)

    @property
    def ctrl_meas(self):
        """Return (raw) value of ctrl_meas register."""
        return self._bus.read_byte_data(self.addr, self.CTRL_MEAS)

    def _ctrl_meas_set(self, osrs_t, osrs_p, mode):
        """Set ctrl_meas register (for internal use)."""
        data = (osrs_t << 5) + (osrs_p << 2) + mode
        self._bus.write_byte_data(self.addr, self.CTRL_MEAS,
                                  data)

    def set_acquisition_options(self, temperature_oversampling,
                                pressure_oversampling, mode):
        """Set acquisition options."""
        to = temperature_oversampling
        po = pressure_oversampling
        if to == 0:
            osrs_t = self.OVERSAMPLING_SKIPPED
        elif to == 1:
            osrs_t = self.OVERSAMPLING_1X
        elif to == 2:
            osrs_t = self.OVERSAMPLING_2X
        elif to == 4:
            osrs_t = self.OVERSAMPLING_4X
        elif to == 8:
            osrs_t = self.OVERSAMPLING_8X
        elif to == 16:
            osrs_t = self.OVERSAMPLING_16X
        else:
            raise BMP280Error('Unsupported temperature oversampling')

        if po == 0:
            osrs_p = self.OVERSAMPLING_SKIPPED
        elif po == 1:
            osrs_p = self.OVERSAMPLING_1X
        elif po == 2:
            osrs_p = self.OVERSAMPLING_2X
        elif po == 4:
            osrs_p = self.OVERSAMPLING_4X
        elif po == 8:
            osrs_p = self.OVERSAMPLING_8X
        elif po == 16:
            osrs_p = self.OVERSAMPLING_16X
        else:
            raise BMP280Error('Unsupported pressure oversampling')

        if (mode is None) or (mode == 0) or (mode == 'sleep'):
            mode = self.SLEEP_MODE
        elif (mode == 1) or (mode == 'forced'):
            mode = self.FORCED_MODE
        elif (mode == 2) or (mode == 3) or (mode == 'normal'):
            mode = self.NORMAL_MODE
        else:
            raise BMP280Error('Unknown device mode')

        self._ctrl_meas_set(osrs_t, osrs_p, mode)

    @property
    def config(self):
        """Return (raw) value of config register."""
        return self._bus.read_byte_data(self.addr, self.CONFIG)

    def _config_set(self, t_sb, _filter, spi3w_en):
        """Set config register (for internal use)."""
        data = (t_sb << 5) + (_filter << 2) + spi3w_en
        self._bus.write_byte_data(self.addr, self.CONFIG, data)

    def _set_config_internal(self, t_sb, filter_constant, spi_3wire):
        """Internal configuration function for easier BME280 support."""
        fc = filter_constant
        if (fc == 0) or (fc == 1):
            _filter = self.FILTER_OFF
        elif fc == 2:
            _filter = self.FILTER_2
        elif fc == 4:
            _filter = self.FILTER_4
        elif fc == 8:
            _filter = self.FILTER_8
        elif fc == 16:
            _filter = self.FILTER_16
        else:
            raise BMP280Error('Unsupported filter constant')

        if spi_3wire:
            spi3w_en = 0x01
        else:
            spi3w_en = 0x00

        self._config_set(t_sb, _filter, spi3w_en)

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
            t_sb = self.STANDBY_2000_MS
        elif it == 4000:
            t_sb = self.STANDBY_4000_MS
        else:
            raise BMP280Error('Unsupported inactive time')

        self._set_config_internal(t_sb, inactive_time,
                                  filter_constant, spi_3wire)

    def raw_pressure(self):
        """Return measured pressure (raw data)."""
        data = self._bus.read_i2c_block_data(self.addr, self.PRESS, 3)
        return (data[0] << 12) + (data[1] << 4) + (data[2] >> 4)

    def raw_temperature(self):
        """Return measured temperature (raw data)."""
        data = self._bus.read_i2c_block_data(self.addr, self.TEMP, 3)
        return (data[0] << 12) + (data[1] << 4) + (data[2] >> 4)

    def temperature(self):
        """Return measured temperature in Celsius."""
        adc_T = float(self.raw_temperature())
        var1 = (adc_T / 16384.0 - self.dig_T1 / 1024.0) * self.dig_T2
        var2 = ((adc_T / 131072.0 - self.dig_T1 / 8192.0) *
                (adc_T / 131072.0 - self.dig_T1 / 8192.0)) * self.dig_T3
        self.t_fine = (var1 + var2)
        T = (var1 + var2) / 5120.0
        return round(T, 2)

    def pressure(self, update_temperature=True):
        """Return measured pressure in Pascals."""
        if (self.t_fine is None) or update_temperature:
            self.temperature()
        adc_P = float(self.raw_pressure())
        var1 = (self.t_fine / 2.0) - 64000.0
        var2 = var1 * var1 * self.dig_P6 / 32768.0
        var2 = var2 + var1 * self.dig_P5 * 2.0
        var2 = (var2 / 4.0) + (self.dig_P4 * 65536.0)
        var1 = (self.dig_P3 * var1 * var1 / 524288.0 +
                self.dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.dig_P1
        if var1 == 0.0:
            return 0.0  # Avoid exception caused by division by zero
        p = 1048576.0 - adc_P
        p = (p - (var2 / 4096.0)) * 6250.0 / var1
        var1 = self.dig_P9 * p * p / 2147483648.0
        var2 = p * self.dig_P8 / 32768.0
        p = p + (var1 + var2 + self.dig_P7) / 16.0
        return round(p, 1)
