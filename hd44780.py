from time import sleep

from pcf8574 import PCF8574

class HD44780(object):
    """
    Library for HD44780 LCD display,
    controlled by PCF8574 I2C expander.
    """

    @staticmethod
    def _char_table(char):
        char = str(char)
        if ord(char) in range(0x20,0x7e): # ASCII characters
            return ord(char)
        # CGRAM characters (custom)
        elif char == '⓪':
            return 0x00
        elif char == '①':
            return 0x01
        elif char == '②':
            return 0x02
        elif char == '③':
            return 0x03
        elif char == '④':
            return 0x04
        elif char == '⑤':
            return 0x05
        elif char == '⑥':
            return 0x06
        elif char == '⑦':
            return 0x07
        # CGROM characters
        elif char == '→':
            return 0x7e
        elif char == '←':
            return 0x7f
        elif char == '·':
            return 0xa5
        elif char == '□':
            return 0xdb
        elif char == '°':
            return 0xdf
        elif char == 'α':
            return 0xe0
        elif char == 'β':
            return 0xe2
        elif char == 'ε':
            return 0xe3
        elif char == 'μ':
            return 0xe4
        elif char == 'δ':
            return 0xe5
        elif char == 'ρ':
            return 0xe6
        elif char == '∞':
            return 0xf3
        elif char == 'Ω':
            return 0xf4
        elif char == 'Σ':
            return 0xf6
        elif char == 'π':
            return 0xf7
        elif char == '÷':
            return 0xfd
        else:
            return 0xff # '█'

    def _write_char(self, char):
        char = self._char_table(char)
        self._write_data(char)

    def _write_data(self, data):
        self._write(data, command=False)

    def _write_command(self, data):
        self._write(data, command=True)

    def _write(self, data, command):
        data_list = self.pcf8574.byte2list(data)
        highNibble = data_list[4:8]
        lowNibble = data_list[0:4]
        # Set write mode
        self.pcf8574.write(self.rw, 0, update=False)
        # Select command/data register
        if command:
            self.pcf8574.write(self.rs, 0, update=False)
        else:
            self.pcf8574.write(self.rs, 1, update=False)
        # Write high nibble
        self.pcf8574.write(self.d4, highNibble[0], update=False)
        self.pcf8574.write(self.d5, highNibble[1], update=False)
        self.pcf8574.write(self.d6, highNibble[2], update=False)
        self.pcf8574.write(self.d7, highNibble[3], update=False)
        self._pulse_enable()
        # Write low nibble
        self.pcf8574.write(self.d4, lowNibble[0], update=False)
        self.pcf8574.write(self.d5, lowNibble[1], update=False)
        self.pcf8574.write(self.d6, lowNibble[2], update=False)
        self.pcf8574.write(self.d7, lowNibble[3], update=False)
        self._pulse_enable()

    def _read(self, command):
        # # Set read mode
        # self.pcf8574.write(self.rw, 1, update=False)
        # # Select command/data register
        # if command:
        #     self.pcf8574.write(self.rs, 0, update=False)
        # else:
        #     self.pcf8574.write(self.rs, 1, update=False)
        # # TODO: rest
        raise NotImplementedError('Read not implemented')

    def _pulse_enable(self):
        self.pcf8574.update()
        self.pcf8574.write(self.en, 1)
        sleep(5e-7) # >450ns
        self.pcf8574.write(self.en, 0)
        sleep(5e-5) # >37us

    def __init__(self, address=0x27, bus=None,
                 en=2, rw=1, rs=0, d4=4, d5=5, d6=6, d7=7,
                 backlight = 3):
        """
        Create object representing HD44780 display.

        The order of the parameters is the same as
        the common Arduino library with the addition of
        a bus parameter after the I2C address and a
        backlight pin at the end.
        """
        self.pcf8574 = PCF8574(address, bus)
        self.en = en
        self.rs = rs
        self.rw = rw
        self.d4 = d4
        self.d5 = d5
        self.d6 = d6
        self.d7 = d7
        self.bl = backlight

        # Initialization by Instruction
        # Wait for HD44780 to start
        sleep(0.05) # >40ms
        # Turn everything off first
        self.pcf8574.write_byte(0x00)
        # 8-bit interface - function set
        self.pcf8574.write(self.d7, 0, update=False)
        self.pcf8574.write(self.d6, 0, update=False)
        self.pcf8574.write(self.d5, 1, update=False)
        self.pcf8574.write(self.d4, 1, update=False)
        # First try - wait >4.1ms 
        self._pulse_enable()
        sleep(0.005)
        # Second try - wait >100us 
        self._pulse_enable()
        sleep(0.001)
        # Third try - device stared 
        self._pulse_enable()
        # Set 4-bit mode
        self.pcf8574.write(self.d7, 0, update=False)
        self.pcf8574.write(self.d6, 0, update=False)
        self.pcf8574.write(self.d5, 1, update=False)
        self.pcf8574.write(self.d4, 0, update=False)
        self._pulse_enable()
        # Function set - 4-bit, 2 lines, 5x8 characters
        self._write_command(0x28)
        # Reset display
        self.display()
        self.clear()
        self.mode()
        self.backlight(False)

    def backlight(self, on=True):
        """Turn backlight on or off."""
        self.pcf8574.write(self.bl, on)

    def clear(self):
        """Clear display and return to top left corner."""
        self._write_command(0x01)
        # Slow command - wait for execution
        sleep(0.002)
    
    def home(self):
        """Return to top left corner."""
        self._write_command(0x02)
        # Slow command - wait for execution
        sleep(0.002)

    def write(self, string):
        """
        Write text in current cursor position.
        Custom characters are defined by ⓪-⑦ in text (circled digits)
        """
        string = str(string)
        for char in string:
            self._write_char(char)

    def shift(self, display=False, right=False):
        """Shift cursor/display left/right."""
        dataList = list(reversed([0, 0, 0, 1, display, right, 0, 0]))
        data = self.pcf8574.list2byte(dataList)
        self._write_command(data)

    def position(self, line, pos):
        """Move cursor to specific line and column."""
        line = int(line)
        if line not in range(0,4):
            return
        pos = int(pos)
        if line == 0:
            address = pos
        elif line == 1:
            address = 0x40 + pos
        elif line == 2:
            address = 0x14 + pos
        elif line == 3:
            address = 0x54 + pos
        self._write_command(0x80 + address)

    def display(self, on=True, cursor=False, blink=False):
        """Turn display on or off, set cursor and/or blinking."""
        dataList = list(reversed([0, 0, 0, 0, 1, on, cursor, blink]))
        data = self.pcf8574.list2byte(dataList)
        self._write_command(data)

    def mode(self, increment=True, shift=False):
        """
        Set increment/decrement on character write
        and choose between cursor move or display shift.
        """
        dataList = list(reversed([0, 0, 0, 0, 0, 1, increment, shift]))
        data = self.pcf8574.list2byte(dataList)
        self._write_command(data)

    def create_char(self, num, data):
        """
        Create custom character.

        You can define 8 different characters, numbered 0-7.
        Character is represented by 5x8 point grid, provided
        as list of 8 5-element lists.
        """
        num = int(num)
        if num not in range(0,8):
            return
        address = num << 3
        # Move to CGRAM character location
        self._write_command(0x40 + address)
        for line in data:
            val = self.pcf8574.list2byte(list(reversed([0, 0, 0] + line)))
            self._write_data(val)
        # Move back to DRAM
        self._write_command(0x80)
