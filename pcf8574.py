from i2c import I2CBus

class PCF8574(object):
    """
    Library for PCF8574/74A IO Expander.
    Should also support PCA8574/74A, 
    PCA9674/74A, PCA9670, PCA9672.
    """

    @staticmethod
    def list2byte(list_):
        """Convert list of 8 binary values to byte."""
        byte = 0
        for val in reversed(list_):
            byte += int(bool(val))
            byte <<= 1
        byte >>= 1
        return byte

    @staticmethod
    def byte2list(byte):
        """Convert byte to list of 8 binary values."""
        list_ = []
        for i in range(8):
            val = byte % 2
            list_.append(val)
            byte >>= 1
        return list_

    def __init__(self, address, bus=None):
        """
        Create object representing PCF8574 chip,
        and set all pins to HIGH (input).
        """
        self.address = address
        self._bus = I2CBus(bus)
        self._pins = [1] * 8

    def read_byte(self):
        """Read all pins state (one byte)."""
        return self._bus.read_byte(self.address)

    def write_byte(self, val):
        """Write all pins state (one byte)."""
        self._pins = self.byte2list(val)
        return self._bus.write_byte(self.address, val)

    def read_all(self):
        """Read all pins state (list of 8 values)."""
        byte = self.read_byte()
        list_ = self.byte2list(byte)
        return list_

    def write_all(self, val):
        """Write all pins state (list of 8 values)."""
        list_ = val
        byte = self.list2byte(list_)
        return self.write_byte(byte)

    def read(self, pin):
        """Read one pin state."""
        list_ = self.read_all()
        return list_[pin]

    def write(self, pin, val, update=True):
        """
        Write one pin state.
        
        If update is False, new settings will not be sent.
        Use update() to write data to device.
        """
        list_ = self._pins[:]
        list_[pin] = int(bool(val))
        if update:
            return self.write_all(list_)
        else:
            self._pins = list_

    def update(self):
        """Update device with settings prepaired with write()."""
        list_ = self._pins[:]
        return self.write_all(list_)
