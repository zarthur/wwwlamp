"""Hardware pin interface.

Has a PinDealer class that keeps track of available
"pins" to control.  When PinDealer.get_pin() is called,
a Pin instance is returned.  The Pin instance
has enable, disable, and toggle methods on it. When 
the Pin instance is no longer needed, the close method
should be used to return the "pin" to the PinDealer's
pool of available pins.  This pattern should be followed 
by other hardware modules for use in the controller.

This is the base class from which other hardware
classes should inherit.
"""

class Pin:
    """Pin class allows control over specific hardware
    pin.
    """
    def __init__(self, pin, dealer):
        """Initializes instance and sets pin to disabled
        state.
        """
        self._pin = pin
        self._dealer = dealer
        self.disable()
        self._enabled = False

    def is_enabled(self):
        """Returns True if pin is enabled, False otherwise."""
        return self._enabled

    def close(self):
        """Returns pin to PinDealer's pool of available pins
        and disables functionality of the Pin instance.
        """
        self.dealer.add_pin(self._pin)
        del_attributes = [x for x in dir(self) if not x.startswith('__')]
        for attribute in del_attributes:
            self.__delattr__(attribute)

    def disable(self):
        """Sets _enabled to False.  Functionality should be defined
        in subclass."""
        self._enabled = False

    def enable(self):
        """Sets _enabled to False.  Functionality should be defined
        in subclass."""
        self._enabled = True

    def toggle(self):
        """Toggles the pin's state"""
        if self._enabled:
            self.disable()
        else:
            self.enable()
        self._enabled = not self._enabled

class PinDealer:
    """Distribues available pins for use.  When get_pin() is called,
    returns a Pin instance.  If no  pins are available, returns None.
    """
    def __init__(self, available):
        """Set a list of available pins that can be used to create
        Pin instances.  Subclass should specify _return_class.
        """
        self._available = available

    def add_pin(self, pin):
        """Adds a pin to the pool of available pins."""
        self._available.append(pin)

    def get_pin(self, pin_number=None):
        """Returns a Pin obejct if a pin is available, else None.
        If a pin is specified and available, a Pin with the requested
        number is returned.  If the requested number is unavailable,
        None is returned.  Subclass should specify the correct Pin
        class for return value.
        """
        if pin_number and pin_number in self._available:
            self._available.remove(pin_number)
            return self._return_class(pin_number, self)

        elif self._available:
            return self._return_class(self._available.pop(), self)

        else:
            return None
