from time import sleep

from serial import Serial

class ThermalPrinter(object):
    """Class for thermal printer with serial communication."""

    @staticmethod
    def _txt2bytes(text):
        # TODO: Protection against characters 0x00-0x1f and 0x7f
        return text.encode(encoding='ascii',errors='replace')

    @staticmethod
    def _wait():
        sleep(0.1)

    def __init__(self, port, baudrate=19200, printer=None):
        """
        Create object representing printer.

        Optionally change class used for serial communication.
        """
        if printer is not None:
            self.printer = printer
        else:
            self.printer = Serial(port, baudrate)
        self.reset()

    def reset(self):
        """Reset printer to default state."""
        command = [0x1b, 0x40]
        self.printer.write(bytearray(command))
        self.set_parameters(heating_time=200,heating_interval=50)

    def write(self, text):
        """Print text."""
        text = self._txt2bytes(text)
        for line in text.splitlines(keepends=True):
            self.printer.write(line)
            self._wait()

    def end_printing(self, dots=125):
        """Print buffered text and feed paper."""
        dots = int(dots)
        command = [0x1b, 0x4a, min(max(dots,1),255)]
        self.printer.write(bytearray(command))

    def set_line_spacing(self, dots=None):
        """Set line spacing."""
        if dots is None:
            command = [0x1b, 0x32]
        else:
            dots = int(dots)
            command = [0x1b, 0x33, min(max(dots,1),255)]
        self.printer.write(bytearray(command))

    def set_align(self, align='left'):
        """Set text align."""
        if align in [0, 1, 2]:
            pass
        elif align == 'left':
            align = 0
        elif align == 'middle':
            align = 1
        elif align == 'right':
            align = 2
        else:
            raise KeyError('Unknown align mode')
        command = [0x1b, 0x61, align]
        self.printer.write(bytearray(command))

    def set_print_mode(self, emphasized=False,
        deleteline=False, underline=False):
        """Set printing mode (emphasized, deleteline, underline)."""
        # TODO
        raise NotImplementedError

    def set_updown(self, updown=False):
        """Set upside-down mode."""
        if updown:
            updown = 1
        else:
            updown = 0
        command = [0x1b, 0x7b, updown]
        self.printer.write(bytearray(command))

    def set_reverse_color(self, reverse=False):
        """Set reverse (white-on-black) colors mode."""
        if reverse:
            reverse = 1
        else:
            reverse = 0
        command = [0x1d, 0x42, reverse]
        self.printer.write(bytearray(command))

    # TODO: User-defined characters
    # TODO: Bit-image

    # TODO: Read printer status 
    @property
    def status(self):
        """Get current printer status."""
        raise NotImplementedError

    def set_barcode_chars_position(self, position=None):
        """
        Set barcode human-readable characters position.

        Possible options: none/0, above/1, below/2, both/3.
        """
        if position == 'above' or position == 1:
            position = 1
        elif position == 'below' or position == 2:
            position = 2
        elif position == 'both' or position == 3:
            position = 3
        else:
            position = 0
        command = [0x1d, 0x48, position]
        self.printer.write(bytearray(command))

    def set_barcode_height(self, dots=50):
        """Set barcode height."""
        dots = int(dots)
        command = [0x1d, 0x68, min(max(dots,1),255)]
        self.printer.write(bytearray(command))

    def print_barcode(self, text):
        """
        Print barcode.

        This library supports only CODE128.
        Will set align to 'left'.
        """
        self.set_align('left')
        type_ = 73 # Format 2, CODE128
        text = self._txt2bytes(text)
        text = list(text)
        text = text[:127]
        length = len(text)
        command = [0x1d, 0x6b, type_, length] + text
        self.printer.write(bytearray(command))  

    def set_parameters(self, max_heating_dots=7, heating_time=80,
                       heating_interval=2):
        """
        Set printer parameters: max heating dots,
        heating time, heating interval.
        """
        n1 = min(max(int(max_heating_dots),1),255)
        n2 = min(max(int(heating_time),4),255)
        n3 = min(max(int(heating_interval),1),255)
        command = [0x1b, 0x37, n1, n2, n3]
        self.printer.write(bytearray(command))

    def print_title(self, text):
        """
        Print centered text in border.

        Requires support for non-ascii characters over serial link
        and will reset printer to default state.
        """
        lines = text.splitlines()
        length = len(max(lines, key=len))
        top = [0xC9] + ([0xCD] * length) + [0xBB, ord('\n')]
        left = [0xBA]
        right = [0xBA, ord('\n')]
        bottom = [0xC8] + ([0xCD] * length) + [0xBC, ord('\n')]
        self.reset()
        self.set_align('middle')
        self.set_line_spacing(1)
        self.printer.write(bytearray(top))
        for line in lines:
            difference = length - len(line)
            padding_left = ' ' * (difference // 2)
            padding_right = ' ' * (difference // 2 + difference % 2)
            self.printer.write(bytearray(left))
            self.write(padding_left + line + padding_right)
            self.printer.write(bytearray(right))
        self.printer.write(bytearray(bottom))
        self.reset()


if __name__ == '__main__':
    from random import randint
    printer = ThermalPrinter('/dev/ttyACM0')
    printer.print_title('10 random numbers\n\nSimple printer test?')
    printer.set_align('middle')
    for i in range(10):
        printer.set_reverse_color(i%2)
        printer.write(str(randint(100000000000000, 999999999999999)) + '\n')
    printer.end_printing()
