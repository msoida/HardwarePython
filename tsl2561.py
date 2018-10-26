from i2c import I2CBus, I2CError


class TSL2561Error(I2CError):
    pass


class TSL2561(object):
    """Library for TSL2561 light sensor."""

    I2C_ADDRESS = 0x39

    # Commands
    CMD = 0b1 << 7
    CLEAR = 0b1 << 6
    WORD = 0b1 << 5
    BLOCK = 0b1 << 4

    # Registers
    CONTROL = 0x00
    TIMING = 0x01
    THRESHLOW = 0x02  # - 0x03 (lsb, msb)
    THRESHHIGH = 0x04  # - 0x05 (lsb, msb)
    INTERRUPT = 0x06
    ID = 0x0a
    DATA0 = 0x0c  # - 0x0d (lsb, msb)
    DATA1 = 0x0e  # - 0x0f (lsb, msb)

    def __init__(self, bus=None, addr=None):
        """Create object representing TSL2561 chip."""
        self._bus = I2CBus(bus)
        if addr is not None:
            self.addr = addr
        else:
            self.addr = self.I2C_ADDRESS
        self._gain16 = False

    def power(self, power=True):
        """Turn chip power on or off."""
        if power:
            self._bus.write_byte_data(self.addr, (self.CMD | self.CONTROL), 0x03)
        else:
            self._bus.write_byte_data(self.addr, (self.CMD | self.CONTROL), 0x00)

    def timing(self, gain=1, manual=False, integration_time=0b11):
        self._gain16 = (True if (gain == 16) else False)
        gain = ((1 << 4) if (gain == 16) else 0)
        manual = ((1 << 3) if manual else 0)
        integr = (integration_time & 0b11)  # TODO: Change to dict
        data = gain | manual | integr
        self._bus.write_byte_data(self.addr, (self.CMD | self.TIMING), data)

    def threshold(self, low, high):
        # TODO
        pass

    def interrupt(self, interrupt, persist):
        # TODO
        pass

    def id(self):
        """Return ID."""
        data = self._bus.read_byte_data(self.addr, (self.CMD | self.ID))
        partno = ((data >> 4) & 0xF)
        revno = (data & 0xF)
        return partno, revno

    def data(self):
        """Return measured values (after gain normalization)"""
        data0 = self._bus.read_i2c_block_data(self.addr, (self.CMD | self.DATA0), 2)
        data1 = self._bus.read_i2c_block_data(self.addr, (self.CMD | self.DATA1), 2)
        ch0 = data0[1] * 256 + data0[0]
        ch1 = data1[1] * 256 + data1[0]
        if self._gain16:
            ch0 = ch0 / 16
            ch1 = ch1 / 16
        return ch0, ch1

    def fullspectrum(self):
        """Return full spectrum light in lux (visible + IR)"""
        return self.data()[0]

    def ifrared(self):
        """Return infrared light in lux"""
        return self.data()[1]

    def visible(self):
        """Return visible light in lux"""
        return self.data()[0] - self.data()[1]
