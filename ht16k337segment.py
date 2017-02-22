from ht16k33 import HT16K33, HT16K33Error

class HT16K337Segment(HT16K33):
    """Library for 4x7-segment display powered by HT16K33 multiplexer."""

    DOT = 0x80

    @staticmethod
    def _num2hex(number):
        num = str(number)
        if num == '0':
            return 0x3f
        elif num == '1':
            return 0x06
        elif num == '2':
            return 0x5b
        elif num == '3':
            return 0x4f
        elif num == '4':
            return 0x66
        elif num == '5':
            return 0x6d
        elif num == '6':
            return 0x7d
        elif num == '7':
            return 0x07
        elif num == '8':
            return 0x7f
        elif num == '9':
            return 0x6f
        elif num == '10' or num == 'a' or num == 'A':
            return 0x77
        elif num == '11' or num == 'b' or num == 'B':
            return 0x7c
        elif num == '12' or num == 'c' or num == 'C':
            return 0x39
        elif num == '13' or num == 'd' or num == 'D':
            return 0x5e
        elif num == '14' or num == 'e' or num == 'E':
            return 0x79
        elif num == '15' or num == 'f' or num == 'F':
            return 0x71
        return 0x00

    def __init__(self, address=0x70, bus=None):
        """Create object representing 7 segment display."""
        super().__init__(address, bus)

    def write_buffer(self, data, update=True):
        """Write whole buffer (List with 5 16-bit numbers)."""
        data = data + [0x0000] * 3
        super().write_buffer(data, update)

    def write_digit(self, position, digit, dot=False, update=True):
        register = [0,1,3,4][position]
        if dot:
            data = self._num2hex(digit) | self.DOT
        else:
            data = self._num2hex(digit)
        self.write_word(register, data, update)

    def colon(self, on=True, update=True):
        if on:
            self.write_word(2, 0x02, update)
        else:
            self.write_word(2, 0x00, update)
