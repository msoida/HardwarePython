from struct import unpack

from i2c import I2CBus, I2CError


class AM2315Error(I2CError):
    pass


class AM2315(object):
    """Library for AM2315 temperature & humidity sensor."""

    I2C_ADDRESS = 0x5c

    # Function codes
    READ_REGISTER_DATA = 0x03
    WRITE_MULTIPLE_REGISTERS = 0x10  # not implemented

    # Registers
    HUMIDITY = 0x00  # - 0x01 (msb, lsb)
    TEMPERATURE = 0x02  # - 0x03 (msb, lsb)
    MODEL = 0x08  # - 0x09 (msb, lsb)
    VERSION = 0x0A
    ID = 0x0B  # - 0x0E (msb first, 4 bytes)
    STATUS = 0x0F  # reserved - not implemented
    USERA = 0x10  # - 0x11 (msb, lsb) - not implemented
    USERB = 0x12  # - 0x13 (msb, lsb) - not implemented

    def __init__(self, bus=None):
        """Create object representing AM2315 chip."""
        self._bus = I2CBus(bus)
        self.addr = self.I2C_ADDRESS

    def read_data(self, register, count=1):
        """Read data from sensor (for internal use)."""

        # Sensors uses I2C_ModBus protocol,
        # communication has 2 steps:
        #
        # 1. WRITE command to register 0x03 with start register and count
        # 2. READ command (any register)
        # Response frame: 0x03, len, data, 2xCRC => n+4 bytes
        self._bus.write_i2c_block_data(
            self.I2C_ADDRESS, self.READ_REGISTER_DATA, [register, count])
        rawdata = self._bus.read_i2c_block_data(self.addr, 0x00, count + 4)
        return rawdata[2:-2]

    def humidity(self):
        """Return measured humidity in %."""
        rawdata = self.read_data(self.HUMIDITY, 2)
        data = unpack('>H', rawdata)[0]
        # Humidity is stored as int with one decimal place
        return data / 10

    def temperature(self):
        """Return measured temperature in Celsius."""
        rawdata = self.read_data(self.TEMPERATURE, 2)
        data = unpack('>H', rawdata)[0]

        # Check if negative value bit set
        if data & (1 << 15):
            data &= ((1 << 15) - 1)  # clear negative bit
            data = -data

        # Temperature is stored as int with one decimal place
        return data / 10

    def model(self):
        """Return model no."""
        rawdata = self.read_data(self.MODEL, 2)
        data = unpack('>H', rawdata)[0]
        return data

    def version(self):
        """Return version."""
        rawdata = self.read_data(self.VERSION, 1)
        data = unpack('>B', rawdata)[0]
        return data

    def id(self):
        """Return ID."""
        rawdata = self.read_data(self.ID, 4)
        data = unpack('>I', rawdata)[0]
        return data
