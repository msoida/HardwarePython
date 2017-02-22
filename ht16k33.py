from i2c import I2CBus, I2CError

class HT16K33Error(I2CError):
    pass


class HT16K33(object):
    """Library for HT16K33 I2C LED Driver."""

    # Command registers
    DATA_REGISTER = 0x00
    OSCILLATOR_ON = 0x21
    OSCILLATOR_OFF = 0x20
    DISPLAY_ON = 0x81
    DISPLAY_OFF = 0x80
    DIMMING = 0xe0

    # Blinking modes
    BLINK_OFF = 0x00
    BLINK_2HZ = 0x02
    BLINK_1HZ = 0x04
    BLINK_HALFHZ = 0x06

    def __init__(self, address=0x70, bus=None):
        """Create object representing HT16K33 chip."""
        self.address = address
        self._bus = I2CBus(bus)
        self._buffer = [0x0000] * 8
        self.oscillator(True)
        self.blink(0)
        self.brightness(15)
        self.update()

    def oscillator(self, on=True):
        """Turn on or off internal oscillator."""
        if on:
            self._bus.write_byte(self.address, self.OSCILLATOR_ON)
        else:
            self._bus.write_byte(self.address, self.OSCILLATOR_OFF)

    def update(self, update=True):
        """Update data registers."""
        if not update:
            return
        data = list()
        for i in self._buffer:
            data.append(i & 0xff)
            data.append((i >> 8) & 0xff)
        self._bus.write_i2c_block_data(self.address, self.DATA_REGISTER, data)

    def blink(self, freq=0):
        """
        Set blinking mode.

        Possible values (in Hz): 0 (off), 0.5, 1, 2.
        """
        if freq == 0:
            self._blink = self.BLINK_OFF
        elif freq == 0.5:
            self._blink = self.BLINK_HALFHZ
        elif freq == 1:
            self._blink = self.BLINK_1HZ
        elif freq == 2:
            self._blink = self.BLINK_2HZ
        self.display(True)

    def display(self, on=True):
        """Turn display on or off."""
        if on:
            self._bus.write_byte(self.address, self.DISPLAY_ON | self._blink)
        else:
            self._bus.write_byte(self.address, self.DISPLAY_OFF)

    def brightness(self, brightness=15):
        """Set brightnes level (0-15)"""
        brightness = int(brightness)
        if brightness < 0:
            brightness = 0
        elif brightness > 15:
            brightness = 15
        self._bus.write_byte(self.address, self.DIMMING | brightness)

    def write_word(self, register, data, update=True):
        """Write 16-bit word to register 0-7."""
        register = int(register)
        if register not in range(0,8):
            raise HT16K33Error("Wrong register.")
        self._buffer[register] = data
        self.update(update)

    def write_buffer(self, data, update=True):
        """Write whole buffer (List with 8 16-bit numbers)."""
        if len(data) != 8:
            raise HT16K33Error("Wrong buffer length.")
        self._buffer = [int(i) for i in data]
        self.update(update)
