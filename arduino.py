"""Arduino pin interface.

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

Because a serial interface has to be used with each "pin",
PinDealer must be initialized with a port and it passes
an additional "ser" Serial object to Pin instances.

Because pins are controlled via different strings, an
available pin and used pin should be a tuple.  Thus,
an example of available pins: [('0', '1'), ('o', 'c')],
with the disabling string first.
"""

import serial

import hardware


class Pin(hardware.Pin):
    """Pin class allows control over specific hardware
    "pin".
    """
    def __init__(self, pin, dealer):
        """Initialize the Pin instance and sets the pin
        to a disabled state.
        """
        self._ser = dealer.get_ser()
        self._disable, self._enable = pin
        super().__init__(pin, dealer)

    def enable(self):
        """Enables the pin"""
        self._ser.write(self._enable.encode())
        super().enable()

    def disable(self):
        """Disables the pin"""
        self._ser.write(self._disable.encode())
        super().disable()


class PinDealer(hardware.PinDealer):
    """Returns a Pin obejct if a pin is available, else None.
    If a pin is specified, using its on/off string tuple, and
    available, a Pin is returned.  If the requested number is
    unavailable, None is returned.
    """
    def __init__(self, available, port):
        """Set a list of available on/off tuples that can be used
        to create Pin instances.
        """
        self._ser = serial.Serial(port, 9600)
        self._return_class = Pin
        super().__init__(available)

    def get_ser(self):
        """Returns Serial object associated with the port
        passed to the PinDealer class.
        """
        return self._ser
