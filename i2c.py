"""
This module defines an object type that allows SMBus transactions
on hosts running the Linux kernel.  The host kernel must have I2C
support, I2C device interface support, and a bus adapter driver.
All of these can be either built-in to the kernel, or loaded from
modules.

Because the I2C device interface is opened R/W, users of this
module usually must have root permissions.
"""


# Kernel module documentation:
# https://git.kernel.org/cgit/linux/kernel/git/torvalds/
#     linux.git/plain/Documentation/i2c/smbus-protocol


from re import match as re_match
try:
    from typing import List
except ImportError as err:
    raise ImportError(
        'Typing module must be manually installed on Python < 3.5') from err

try:
    from smbus import SMBus
except ImportError as err:
    raise ImportError('No SMBus module') from err


def _getPiRevision() -> int:
    """Get the version number of the Raspberry Pi board."""
    # Revision list available at:
    # http://elinux.org/RPi_HardwareHistory#Board_Revision_History
    try:
        with open('/proc/cpuinfo', 'r') as infile:
            for line in infile:
                # Match a line of the form "Revision : 0002"
                # while ignoring extra info in front of the revision
                # (like 1000 when the Pi was over-volted).
                match = re_match('Revision\s+:\s+.*(\w{4})$', line)
                if match and match.group(1) in ['0000', 
                                                '0002', '0003']:
                    # Return revision 1 if revision
                    # ends with 0000, 0002 or 0003.
                    return 1
                elif match:
                    # Assume revision 2 if revision
                    # ends with any other 4 chars.
                    return 2
            # Couldn't find the revision, assume revision 0 (not Pi)
            return 0
    except:
        return 0


class I2CError(OSError):
    pass


class I2CBus(object):

    """
    SMBus object that is (optionally) connected to the
    specified I2C device interface.

    On Raspberry Pi automatically connects to proper interface.
    On other systems I2C bus number must be specified for automatic
    connection.
        
    Bus number -1 disables automatic connection on Raspberry Pi.
    """

    @staticmethod
    def _error(addr, err):
        if err.errno == 5:
            return I2CError(err.errno,
                'Error accessing address {}: I2C device not responding'.format(
                hex(addr)))
        # if err.errno == 9:
        return I2CError(err.errno,
            'Error accessing address {}: I2C bus not open'.format(
            hex(addr)))

    @staticmethod
    def reverseByteOrder(data: int) -> int:
        """Reverses the byte order of a 16-bit value"""
        # Courtesy Vishal Sapre
        val = 0
        for i in range(2):
            val = (val << 8) | (data & 0xff)
            data >>= 8
        return val

    @staticmethod
    def getPiI2CBusNumber() -> int:
        """
        Get the I2C bus number of the Raspberry Pi board,
        or -1 if cannot be determined (not Rasperry Pi).
        """
        rev = _getPiRevision()
        if rev > 1:
            return 1
        elif rev == 1:
            return 0
        return -1

    @property
    def pec(self):
        """
        True if Packet Error Codes (PEC) are enabled.

        PEC adds a CRC-8 error-checking byte to transfers using it,
        immediately before the terminating STOP.
        """
        return self.bus.pec

    @pec.setter
    def pec(self, val):
        self.bus.pec = val

    @pec.deleter
    def pec(self):
        raise TypeError('Cannot delete attribute')

    def __init__(self, bus: int=None) -> None:
        if bus is None:
            bus = self.getPiI2CBusNumber()

        if bus != -1:
            try:
                self.bus = SMBus(bus)
            except FileNotFoundError as err:
                raise FileNotFoundError('Specified I2C bus not found') from err
            except OSError as err:
                raise I2CError(err.errno, 'Could not connect to I2C bus') from err
        else:
            self.bus = SMBus()

    def open(self, bus: int) -> None:
        """Connect the object to the specified SMBus."""
        try:
            self.bus.open(bus)
        except FileNotFoundError as err:
            raise FileNotFoundError('Specified I2C bus not found') from err
        except OSError as err:
            raise I2CError(err.errno, 'Could not connect to I2C bus') from err

    def close(self) -> None:
        """Disconnect the object from the bus."""
        self.bus.close()

    # SMBus Access
    def write_quick(self, addr: int) -> None:
        """
        Perform SMBus Quick transaction.

        This sends a single bit to the device,
        at the place of the Rd/Wr bit.
        """
        try:
            return self.bus.write_quick(addr)
        except OSError as err:
            raise self._error(addr, err) from err

    def read_byte(self, addr: int) -> int:
        """
        Perform SMBus Read Byte transaction.

        This reads a single byte from a device,
        without specifying a device register.
        Some devices are so simple that this interface is enough;
        for others, it is a shorthand if you want to read
        the same register as in the previous SMBus command.
        """
        try:
            return self.bus.read_byte(addr)
        except OSError as err:
            raise self._error(addr, err) from err

    def write_byte(self, addr: int, val: int) -> None:
        """
        Perform SMBus Write Byte transaction.

        This operation is the reverse of Receive Byte:
        it sends a single byte to a device.
        See Receive Byte for more information.
        """
        try:
            return self.bus.write_byte(addr, val)
        except OSError as err:
            raise self._error(addr, err) from err

    def read_byte_data(self, addr: int, cmd: int) -> int:
        """
        Perform SMBus Read Byte Data transaction.

        This reads a single byte from a device,
        from a designated register.
        The register is specified through the Comm byte.
        """
        try:
            return self.bus.read_byte_data(addr, cmd)
        except OSError as err:
            raise self._error(addr, err) from err

    def write_byte_data(self, addr: int, cmd: int, val: int) -> None:
        """
        Perform SMBus Write Byte Data transaction.

        This writes a single byte to a device,
        to a designated register. The register is specified
        through the Comm byte. This is the opposite of
        the Read Byte operation.
        """
        try:
            return self.bus.write_byte_data(addr, cmd, val)
        except OSError as err:
            raise self._error(addr, err) from err

    def read_word_data(self, addr: int, cmd: int) -> int:
        """
        Perform SMBus Read Word Data transaction.

        This operation is very like Read Byte;
        again, data is read from a device, from a designated register
        that is specified through the Comm byte.
        But this time, the data is a complete word (16 bits).
        """
        try:
            return self.bus.read_word_data(addr, cmd)
        except OSError as err:
            raise self._error(addr, err) from err

    def write_word_data(self, addr: int, cmd: int, val: int) -> None:
        """
        Perform SMBus Write Word Data transaction.

        This is the opposite of the Read Word operation. 16 bits
        of data is written to a device, to the designated register
        that is specified through the Comm byte.
        """
        try:
            return self.bus.write_word_data(addr, cmd, val)
        except OSError as err:
            raise self._error(addr, err) from err

    def read_word_swapped(self, addr: int, cmd: int) -> int:
        """
        Perform SMBus Read Word Data transaction,
        where the two data bytes are the other way around
        (not SMBus compliant, but very popular.)
        """
        val = self.read_word_data(addr, cmd)
        return self.reverseByteOrder(val)

    def write_word_swapped(self, addr: int, cmd: int, val: int) -> None:
        """
        Perform SMBus Write Word Data transaction,
        where the two data bytes are the other way around
        (not SMBus compliant, but very popular.)
        """
        val = self.reverseByteOrder(val)
        return self.write_word_data(addr, cmd, val)

    def process_call(self, addr: int, cmd: int, val: int) -> None:
        """
        Perform SMBus Process Call transaction.

        This command selects a device register (through the Comm byte),
        sends 16 bits of data to it,
        and reads 16 bits of data in return.
        """
        try:
            return self.bus.process_call(addr, cmd, val)
        except OSError as err:
            raise self._error(addr, err) from err

    def read_block_data(self, addr: int, cmd: int) -> List[int]:
        """
        Perform SMBus Read Block Data transaction.

        This command reads a block of up to 32 bytes from a device,
        from a designated register that is specified
        through the Comm byte. The amount of data
        is specified by the device in the Count byte.
        """
        try:
            return self.bus.read_block_data(addr, cmd)
        except OSError as err:
            raise self._error(addr, err) from err

    def write_block_data(self, addr: int, cmd: int, vals: List[int]) -> None:
        """
        Perform SMBus Write Block Data transaction.

        The opposite of the Block Read command,
        this writes up to 32 bytes to a device,
        to a designated register that is specified through the
        Comm byte. The amount of data is specified in the Count byte.
        """
        try:
            return self.bus.write_block_data(addr, cmd, vals)
        except OSError as err:
            raise self._error(addr, err) from err

    def block_process_call(self, addr: int, cmd: int,
        vals: List[int]) -> List[int]:
        """
        Perform SMBus Block Process Call transaction.

        This command selects a device register (through the Comm byte),
        sends 1 to 31 bytes of data to it, and reads 1 to 31 bytes
        of data in return.
        """
        try:
            return self.bus.block_process_call(addr, cmd, vals)
        except OSError as err:
            raise self._error(addr, err) from err

    # I2C Access
    def read_i2c_block_data(self, addr: int, cmd: int,
        len: int=32) -> List[int]:
        """
        Perform I2C Block Read transaction.

        This command reads a block of bytes from a device, from a 
        designated register that is specified through the Comm byte.
        """
        try:
            return self.bus.read_i2c_block_data(addr, cmd, len)
        except OSError as err:
            raise self._error(addr, err) from err

    def write_i2c_block_data(self, addr: int, cmd: int,
        vals: List[int]) -> None:
        """
        Perform I2C Block Write transaction.

        The opposite of the Block Read command, this writes bytes to 
        a device, to a designated register that is specified through the
        Comm byte. Note that command lengths of 0, 2, or more bytes are
        supported as they are indistinguishable from data.
        """
        try:
            return self.bus.write_i2c_block_data(addr, cmd, vals)
        except OSError as err:
            raise self._error(addr, err) from err
