"""RaspberryPI GPIO pin interface.

Inherits from generic hardware interface in
hardware.py.

Has a PinDealer class that keeps track of available
"pins" to control.  When PinDealer.get_pin() is called,
a Pin instance is returned.  The Pin instance
has enable, disable, and toggle methods on it. When
the Pin instance is no longer needed, the close method
should be used to return the "pin" to the PinDealer's
pool of available pins.  This pattern should be followed
by other hardware modules for use in the controller.

Example of available pins: [8, 9]

see http://elinux.org/RPi_Low-level_peripherals for
pin details.
"""

import RPi.GPIO as GPIO

import hardware

GPIO.setmode(GPIO.BCM)


class Pin(hardware.Pin):
    """Pin class allows control over specific hardware
    pin.
    """
    def __init__(self, pin, dealer):
        """Initialize the Pin instance and sets the pin
        to a disabled state.
        """
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, False)
        super().__init__(pin, dealer)

    def enable(self):
        """Enables the pin"""
        GPIO.output(self._pin, True)
        super().enable()

    def disable(self):
        """Disables the pin"""
        GPIO.output(self._pin, False)
        super().disable()


class PinDealer(hardware.PinDealer):
    """Returns a Pin obejct if a pin is available, else None.
    If a pin is specified and available, a Pin with the requested
    number is returned.  If the requested number is unavailable,
    None is returned.
    """
    def __init__(self, pin_number=None, port=None):
        """Set a list of available pins that can be used to create
        Pin instances.
        """
        self._return_class = Pin
        super().__init__(pin_number)
