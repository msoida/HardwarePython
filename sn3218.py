from i2c import I2CBus, I2CError

class SN3218Error(I2CError):
    pass


class SN3218(object):
    """Library for SN3218."""

    I2C_ADDRESS = 0x54

    # Command registers
    ENABLE_OUTPUT = 0x00
    CHANNEL = 0x01 # - 0x12 (1-18)
    ENABLE_LEDS = 0x13 #, 0x14, 0x15
    UPDATE = 0x16
    RESET = 0x17

    _gamma_table = [
        0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
        1,1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,3,3,3,3,3,3,3,3,3,
        3,3,3,3,4,4,4,4,4,4,4,4,4,4,4,5,5,5,5,5,5,5,5,6,6,6,6,6,6,6,
        7,7,7,7,7,7,8,8,8,8,8,8,9,9,9,9,10,10,10,10,10,11,11,11,11,
        12,12,12,13,13,13,13,14,14,14,15,15,15,16,16,16,17,17,18,18,
        18,19,19,20,20,20,21,21,22,22,23,23,24,24,25,26,26,27,27,28,
        29,29,30,31,31,32,33,33,34,35,36,36,37,38,39,40,41,42,42,43,
        44,45,46,47,48,50,51,52,53,54,55,57,58,59,60,62,63,64,66,67,
        69,70,72,74,75,77,79,80,82,84,86,88,90,91,94,96,98,100,102,
        104,107,109,111,114,116,119,122,124,127,130,133,136,139,142,
        145,148,151,155,158,161,165,169,172,176,180,184,188,192,196,
        201,205,210,214,219,224,229,234,239,244,250,255,
        ]

    @classmethod
    def _correct_value(cls, value, gamma):
        v = int(value)
        if v<0:
            v=0
        if v>255:
            v=255
        if gamma:
            return cls._gamma_table[v]
        else:
            return v

    def _channel_output(self, update):
        chA = 0
        chB = 0
        chC = 0
        for channel in self._channel_enable[6:0:-1]:
            chA += int(bool(channel))
            chA <<= 1
        chA >>= 1
        for channel in self._channel_enable[12:5:-1]:
            chB += int(bool(channel))
            chB <<= 1
        chB >>= 1
        for channel in self._channel_enable[18:12:-1]:
            chC += int(bool(channel))
            chC <<= 1
        chC >>= 1
        self._bus.write_i2c_block_data(self.I2C_ADDRESS, self.ENABLE_LEDS,
                                       [chA, chB, chC])
        self.update(update)

    def __init__(self, bus=None):
        """Create object representing SN3218 chip."""
        self._bus = I2CBus(bus)
        self._channel_enable = [0] * 19

    def output(self, enable):
        """Enable or disable output."""
        if enable:
            val = 0x01
        else:
            val = 0x00
        self._bus.write_byte_data(self.I2C_ADDRESS, self.ENABLE_OUTPUT, val)

    def update(self, update=True):
        """Update internal registers with sent values."""
        if update:
            self._bus.write_byte_data(self.I2C_ADDRESS, self.UPDATE, 0xff)

    def reset(self):
        """Reset all internal registers."""
        self._bus.write_byte_data(self.I2C_ADDRESS, self.RESET, 0xff)

    def channel_output(self, channel, enable, update=True):
        """Enable or disable specific channel."""
        channel = int(channel)
        if (channel < 1) or (channel > 18):
            raise SN3218Error("Unknown channel number")
        if enable:
            val = 1
        else:
            val = 0
        self._channel_enable[channel] = val
        self._channel_output(update)

    def channel_mask(self, mask, update=True):
        """Set channel output mask (list with 18 elements)."""
        mask = list(mask)
        if len(mask) != 18:
            raise SN3218Error("Wrong mask length")
        self._channel_enable = [0] + [int(i) for i in mask]
        self._channel_output(update)

    def channel(self, channel, value, gamma=True, update=True):
        """Set channel PWM output."""
        channel = int(channel)
        if channel not in range(1,19):
            raise SN3218Error("Unknown channel number")
        value = self._correct_value(value, gamma)
        self._bus.write_byte_data(self.I2C_ADDRESS, channel, value)
        self.update(update)

    def all(self, value, gamma=True, update=True):
        """Set all channels PWM output."""
        value = self._correct_value(value, gamma)
        self._bus.write_i2c_block_data(self.I2C_ADDRESS, self.CHANNEL,
                                       ([value] * 18))
        self.update(update)
