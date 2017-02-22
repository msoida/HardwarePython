"""
This module defines an object type that allows SPI transactions
on hosts running the Linux kernel. The host kernel must have SPI
support and SPI device interface support.
All of these can be either built-in to the kernel, or loaded from
modules.

Because the SPI device interface is opened R/W, users of this
module usually must have root permissions.
"""

try:
    from typing import List
except ImportError as err:
    raise ImportError(
        'Typing module must be manually installed on Python < 3.5') from err

try:
    from spidev import SpiDev
except ImportError as err:
    raise ImportError('No spidev module') from err


class SPIError(OSError):
    pass


class SPI(object):

    """
    SPI object that is (optionally) connected to the
    specified SPI device interface.
    """

    @property
    def bits_per_word(self):
        """bits per word"""
        return self.dev.bits_per_word

    @bits_per_word.setter
    def bits_per_word(self, val):
        self.dev.bits_per_word = val

    @bits_per_word.deleter
    def bits_per_word(self):
        raise TypeError('Cannot delete attribute')

    @property
    def cshigh(self):
        """CS active high"""
        return self.dev.cshigh

    @cshigh.setter
    def cshigh(self, val):
        self.dev.cshigh = val

    @cshigh.deleter
    def cshigh(self):
        raise TypeError('Cannot delete attribute')

    @property
    def loop(self):
        """loopback configuration"""
        return self.dev.loop

    @loop.setter
    def loop(self, val):
        self.dev.loop = val

    @loop.deleter
    def loop(self):
        raise TypeError('Cannot delete attribute')

    @property
    def lsbfirst(self):
        """LSB first"""
        return self.dev.lsbfirst

    @lsbfirst.setter
    def lsbfirst(self, val):
        self.dev.lsbfirst = val

    @lsbfirst.deleter
    def lsbfirst(self):
        raise TypeError('Cannot delete attribute')

    @property
    def max_speed_hz(self):
        """maximum speed in Hz"""
        return self.dev.max_speed_hz

    @max_speed_hz.setter
    def max_speed_hz(self, val):
        self.dev.max_speed_hz = val

    @max_speed_hz.deleter
    def max_speed_hz(self):
        raise TypeError('Cannot delete attribute')

    @property
    def mode(self):
        """
        SPI mode as two bit pattern of
        Clock Polarity  and Phase [CPOL|CPHA]
        min: 0b00 = 0 max: 0b11 = 3
        """
        return self.dev.mode

    @mode.setter
    def mode(self, val):
        self.dev.mode = val

    @mode.deleter
    def mode(self):
        raise TypeError('Cannot delete attribute')

    @property
    def threewire(self):
        """SI/SO signals shared"""
        return self.dev.threewire

    @threewire.setter
    def threewire(self, val):
        self.dev.threewire = val

    @threewire.deleter
    def threewire(self):
        raise TypeError('Cannot delete attribute')

    def __init__(self, bus: int=None, client: int=None) -> None:
        if bus is not None and client is not None:
            try:
                self.dev = SpiDev(bus, client)
            except FileNotFoundError as err:
                raise FileNotFoundError('Specified SPI bus/device not found') from err
            except OSError as err:
                raise SPIError(err.errno, 'Could not connect to SPI bus') from err
        else:
            self.dev = SpiDev()

    def close(self) -> None:
        """Disconnects the object from the interface."""
        self.dev.close()

    def fileno(self) -> int:
        """This is needed for lower-level file interfaces, such as os.read()."""
        return self.dev.fileno()

    def open(self, bus: int, device: int) -> None:
        """
        Connects the object to the specified SPI device.
        open(X,Y) will open /dev/spidev-X.Y
        """
        try:
            self.dev.open(bus, device)
        except FileNotFoundError as err:
            raise FileNotFoundError(
                'Specified SPI bus/device not found') from err
        except OSError as err:
            raise SPIError(err.errno, 'Could not connect to SPI bus') from err

    def readbytes(self, len: int) -> List[int]:
        """Read len bytes from SPI device."""
        try:
            return self.dev.readbytes(len)
        except OSError as err:
            raise SPIError(err.errno, 'SPI device not open') from err

    def writebytes(self, values: List[int]) -> None:
        """Write bytes to SPI device."""
        try:
            return self.dev.writebytes(values)
        except OSError as err:
            raise SPIError(err.errno, 'SPI device not open') from err
        except SystemError as err:
            raise TypeError('argument must be a list') from err

    def xfer(self, values: List[int]) -> List[int]:
        """
        Perform SPI transaction.
        CS will be released and reactivated between blocks.
        delay specifies delay in usec between blocks.
        """
        try:
            return self.dev.xfer(values)
        except OSError as err:
            raise SPIError(err.errno, 'SPI device not open') from err
        except SystemError as err:
            raise TypeError('argument must be a list') from err

    def xfer2(self, values: List[int]) -> List[int]:
        """
        Perform SPI transaction.
        CS will be held active between blocks.
        """
        try:
            return self.dev.xfer2(values)
        except OSError as err:
            raise SPIError(err.errno, 'SPI device not open') from err
        except SystemError as err:
            raise TypeError('argument must be a list') from err
