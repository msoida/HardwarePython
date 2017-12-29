# from ctypes import c_short, c_ushort
from i2c import I2CBus, I2CError


class INA219Error(I2CError):
    pass


class INA219(object):
    """Library for INA219 high-side voltage & current sensor."""

    # I2C_ADDRESS = 0x40 - 0x4f (configurable)

    # Registers
    CONFIG = 0x00  # read/write
    SHUNT_VOLTAGE = 0x01  # read only
    BUS_VOLTAGE = 0x02  # read only
    POWER = 0x03  # read only
    CURRENT = 0x04  # read only
    CALIBRATION = 0x05  # read/write

    # Constants
    RESET = (1 << 15)  # reset bit of config register
    SUPPORTED_MODE = [0, 1, 2, 3, 4, 5, 6, 7]
    SUPPORTED_ADC = [9, 10, 11, 12, 2, 4, 8, 16, 32, 64, 128]
    SUPPORTED_GAIN = [1, 2, 4, 8]
    SUPPORTED_VRANGE = [16, 32]

    @staticmethod
    def _get_ADC(value) -> int:
        if value == 9:
            ADC = 0x0
        elif value == 10:
            ADC = 0x1
        elif value == 11:
            ADC = 0x2
        elif value == 12:
            ADC = 0x3
        elif value == 2:
            ADC = 0x9
        elif value == 4:
            ADC = 0x10
        elif value == 8:
            ADC = 0x11
        elif value == 16:
            ADC = 0x12
        elif value == 32:
            ADC = 0x13
        elif value == 64:
            ADC = 0x14
        elif value == 128:
            ADC = 0x15
        else:
            raise INA219Error('Unsupported ADC mode')
        return ADC

    def __init__(self, bus=None, address=0x40) -> None:
        """Create object representing INA219 chip."""
        self._bus = I2CBus(bus)
        self.addr = address
        self._init_params()

    def _init_params(self) -> None:
        """Initialize parameters to default values (for internal use)."""
        self._mode = 7
        self._shuntADC = 12
        self._busADC = 12
        self._gain = 8
        self._vrange = 32

        self._currentLSB = 0
        self._powerLSB = 0
        self._calibration = 0

    def mode(self, value=None, update=True) -> int:
        """
        Get or set operating mode.
        Can have following values:
        0 -> Power-Down
        1 -> Shunt Voltage, Triggered
        2 -> Bus Voltage, Triggered
        3 -> Shunt and Bus, Triggered
        4 -> ADC Off (disabled)
        5 -> Shunt Voltage, Continuous
        6 -> Bus Voltage, Continuous
        7 -> Shunt and Bus, Continuous (default)
        """
        if value is not None:
            if value not in self.SUPPORTED_MODE:
                raise INA219Error('Unsupported mode')
            self._mode = value
            if update:
                self._config_set()
        return self._mode

    def shuntADC(self, value=None, update=True) -> int:
        """
        Get or set shunt ADC mode.
        Can have following values:
        9, 10, 11 or 12 for selecting x-bit mode
        2, 4, 8, 16, 32, 64, 128 for selecting x-sample mode
        12-bit mode is selected by default.
        """
        if value is not None:
            if value not in self.SUPPORTED_ADC:
                raise INA219Error('Unsupported shunt ADC mode')
            self._shuntADC = value
            if update:
                self._config_set()
        return self._shuntADC

    def busADC(self, value=None, update=True) -> int:
        """
        Get or set bus ADC mode.
        Can have following values:
        9, 10, 11 or 12 for selecting x-bit mode
        2, 4, 8, 16, 32, 64, 128 for selecting x-sample mode
        12-bit mode is selected by default.
        """
        if value is not None:
            if value not in self.SUPPORTED_ADC:
                raise INA219Error('Unsupported bus ADC mode')
            self._busADC = value
            if update:
                self._config_set()
        return self._busADC

    def gain(self, value=None, update=True) -> int:
        """
        Get or set gain.
        Can have following values:
        1 -> 40mV range
        2 -> 80mV range
        4 -> 160mV range
        8 -> 320mV range (default)
        """
        if value is not None:
            if value not in self.SUPPORTED_GAIN:
                raise INA219Error('Unsupported gain')
            self._gain = value
            if update:
                self._config_set()
        return self._gain

    def vrange(self, value=None, update=True) -> int:
        """Get or set voltage range. Can be 16V or 32V (default)."""
        if value is not None:
            if value not in self.SUPPORTED_VRANGE:
                raise INA219Error('Unsupported voltage range')
            self._vrange = value
            if update:
                self._config_set()
        return self._vrange

    def _config_set(self) -> None:
        """Set config register (for internal use)."""
        SADC = self._get_ADC(self._shuntADC)
        BADC = self._get_ADC(self._busADC)

        if self._gain == 1:
            PG = 0x0
        elif self._gain == 2:
            PG = 0x1
        elif self._gain == 4:
            PG = 0x2
        elif self._gain == 8:
            PG = 0x3
        else:
            raise INA219Error('Unsupported gain')

        BRNG = (0 if (self._vrange == 16) else 1)

        data = (self._mode & 0x7)  # mode (3 bits)
        data += ((SADC & 0xf) << 3)  # SADC (4 bits)
        data += ((BADC & 0xf) << 7)  # BADC (4 bits)
        data += ((PG & 0xf) << 11)  # PG (2 bits)
        data += ((BRNG & 0x1) << 13)  # BRNG (1 bit)
        self._bus.write_word_swapped(self.addr, self.CONFIG, data)

    def reset(self) -> None:
        """Reset INA219 chip."""
        self._bus.write_word_swapped(self.addr, self.CONFIG, self.RESET)
        self._init_params()

    def shunt_voltage(self) -> float:
        """Return shunt voltage (between V+ and V-) in Volts."""
        value = self._bus.read_word_swapped(self.addr, self.SHUNT_VOLTAGE)
        value *= 0.00001  # 0.01mV
        return value

    def bus_voltage(self) -> float:
        """Return bus voltage (between V- and GND) in Volts."""
        value = self._bus.read_word_swapped(self.addr, self.BUS_VOLTAGE)
        # ovf = bool(value & 0x1)  # overflow bit
        # cnvr = bool(value & 0x2)  # conversion ready bit
        value >>= 3
        value *= 0.004  # LSB = 4mV
        return value

    def power(self) -> float:
        """Return estimated power used by connected device."""
        self._set_calibration()  # prevent wrong result
        value = self._bus.read_word_swapped(self.addr, self.POWER)
        value *= self._powerLSB
        return value

    def current(self) -> float:
        """Return current through the shunt resistor in milliamps."""
        self._set_calibration()  # prevent wrong result
        value = self._bus.read_word_swapped(self.addr, self.CURRENT)
        value *= self._currentLSB
        return value

    def _set_calibration(self) -> None:
        """Write calibration register value (for internal use)"""
        self._bus.write_word_swapped(self.addr,
                                     self.CALIBRATION, self._calibration)

    def set_calibration(self, voltage=32, current=2) -> None:
        """
        Set measurement range and precision.
        WORK IN PROGRESS. For now only 32V, 2A mode is supported.
        Possible values:
          32V, 2A (0.8mA precision, overflow at 3.2A)
          32V, 1A (0.4mA precision, overflow at 1.3A)
          16V, 400mA (0.1mA precision, overflow at 1.6A)
        """
        self._currentLSB = 0.04
        self._powerLSB = 0.0008
        self._calibration = 10240
        self._set_calibration()
