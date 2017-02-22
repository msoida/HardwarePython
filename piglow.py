from time import sleep

from sn3218 import SN3218, SN3218Error

class PiGlow(SN3218):
    """Library for Pimoroni PiGlow."""

    _leds = [0x00,
        0x07, 0x08, 0x09, 0x06, 0x05, 0x0a, # arm1 (top)
        0x12, 0x11, 0x10, 0x0e, 0x0c, 0x0b, # arm2 (right)
        0x01, 0x02, 0x03, 0x04, 0x0f, 0x0d, # arm3 (left)
        ]

    @classmethod
    def _correct_led(cls, index):
        return cls._leds[index]

    def __init__(self, bus=None):
        """Create object representing Piglow."""
        super().__init__(bus)
        self.output(True)
        self.channel_mask([1]*18)

    def led(self, led, value, gamma=True, update=True):
        """Set LED PWM output."""
        led = int(led)
        channel = self._correct_led(led)
        self.channel(channel, value, gamma, update)

    def white(self, value, gamma=True, update=True):
        """Set white LED PWM output."""
        for led in [6, 12, 18]:
            self.led(led, value, gamma, update=False)
        self.update(update)
    
    def blue(self, value, gamma=True, update=True):
        """Set blue LED PWM output."""
        for led in [5, 11, 17]:
            self.led(led, value, gamma, update=False)
        self.update(update)
    
    def green(self, value, gamma=True, update=True):
        """Set green LED PWM output."""
        for led in [4, 10, 16]:
            self.led(led, value, gamma, update=False)
        self.update(update)
    
    def yellow(self, value, gamma=True, update=True):
        """Set yellow LED PWM output."""
        for led in [3, 9, 15]:
            self.led(led, value, gamma, update=False)
        self.update(update)
    
    def orange(self, value, gamma=True, update=True):
        """Set orange LED PWM output."""
        for led in [2, 8, 14]:
            self.led(led, value, gamma, update=False)
        self.update(update)
    
    def red(self, value, gamma=True, update=True):
        """Set red LED PWM output."""
        for led in [1, 7, 13]:
            self.led(led, value, gamma, update=False)
        self.update(update)
    
    def color(self, color, value, gamma=True, update=True):
        """Set any color LED PWM output."""
        if color == 6 or color == 'white':
            self.white(value, gamma, update)
        elif color == 5 or color == 'blue':
            self.blue(value, gamma, update)
        elif color == 4 or color == 'green':
            self.green(value, gamma, update)
        elif color == 3 or color == 'yellow':
            self.yellow(value, gamma, update)
        elif color == 2 or color == 'orange':
            self.orange(value, gamma, update)
        elif color == 1 or color == 'red':
            self.red(value, gamma, update)
        else:
            raise SN3218Error('Unknown color: ' + color)
    
    def arm(self, arm, value, gamma=True, update=True):
        """Set arm PWM output."""
        if arm == 1:
            leds = range(1,7)
        elif arm == 2:
            leds = range(7,13)
        elif arm == 3:
            leds = range(13,19)
        else:
            raise SN3218Error('Arm number out of range')
        for led in leds:
            self.led(led, value, gamma, update=False)
        self.update(update)


class PiGlowDisplay(PiGlow):
    """Simple status display based on Pimoroni PiGlow"""

    def startup(self):
        for i in [1,2,3,4,5,  7,8,9,10,11,  13,14,15,16,17]:
            self.led(i,100)
            sleep(1)
        sleep(1)
        for i in range(1,5):
            self.color(i,0)
            sleep(1.5)
        self.blue(0)
        self.white(100)
        sleep(2)
        self.red(50)
        self.white(75)
        sleep(2)
        self.white(50)
        self.yellow(50)
        sleep(3)

    def shutdown(self, full=False):
        if full:
            for i in range(1,7):
                self.color(i,100)
                sleep(0.2)
            for i in range(5,1,-1):
                self.color(i,0)
                sleep(0.4)
            sleep(0.2)
        self.all(0)
        self.red(1)
    
    def error(self):
        self.all(0)
        for i in range(5):
            self.orange(0)
            sleep(1)
            self.orange(100)
            sleep(1)
    
    def wait(self, message=False):
        if message:
            for i in range(5):
                self.white(100)
                sleep(1)
                self.white(0)
                sleep(1)
        else:
            sleep(10)
    
    def ok(self, message=False):
        self.all(0, update=False)
        self.green(50, update=False)
        self.update()
        self.wait(message)
    
    def warning(self, message=False):
        self.all(0, update=False)
        self.yellow(100, update=False)
        self.update()
        self.wait(message)

    def off(self, message=False):
        self.all(0, update=False)
        self.red(50, update=False)
        self.update()
        self.wait(message)
    
    def special(self, message=False):
        self.all(0, update=False)
        self.blue(50, update=False)
        self.update()
        self.wait(message)
    
    def percent(self, number,white=False):
        number = int(number)
        if number < 0:
            number = 0
        if number > 100:
            number = 100
        self.all(0, update=False)
        for i in range(5):
            if number >= (i*20):
                self.color(i+1,50, update=False)
        if white:
            self.white(50, update=False)
        self.update()
        self.wait()
