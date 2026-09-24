"""Thread-safe ownership of lamp hardware, independent of HTTP."""
import threading

ROOMS = ('living', 'bedroom')


class ControllerError(Exception):
    """A command or state read could not be confirmed."""


def validate_updates(updates):
    if (not isinstance(updates, dict) or not updates
            or any(room not in ROOMS or type(value) is not bool
                   for room, value in updates.items())):
        raise ValueError('Expected room names with boolean values')
    return updates


def validate_states(states):
    if (not isinstance(states, dict) or set(states) != set(ROOMS)
            or any(value is not None and type(value) is not bool
                   for value in states.values())):
        raise ValueError('Invalid controller state response')
    return states


class LocalController:
    def __init__(self, pins, cleanup=lambda: None):
        self._pins = pins
        self._cleanup = cleanup
        self._lock = threading.Lock()
        self._states = {room: False for room in ROOMS}
        self._closed = False

    def get_states(self):
        with self._lock:
            if self._closed:
                raise ControllerError('Controller is closed')
            return dict(self._states)

    def set_states(self, updates):
        validate_updates(updates)
        with self._lock:
            if self._closed:
                raise ControllerError('Controller is closed')
            for room, enabled in updates.items():
                try:
                    pin = self._pins[room]
                    (pin.enable if enabled else pin.disable)()
                except Exception as exc:
                    self._states[room] = None
                    raise ControllerError('Hardware command failed for ' + room) from exc
                self._states[room] = enabled
            return dict(self._states)

    def close(self):
        with self._lock:
            if self._closed:
                return
            self._closed = True
            try:
                for room, pin in self._pins.items():
                    try:
                        pin.disable()
                        self._states[room] = False
                    except Exception:
                        self._states[room] = None
            finally:
                self._cleanup()


def create_controller(device):
    """Import hardware dependencies only on the machine owning the pins."""
    if device.lower() == 'debug':
        import hardware
        dealer = hardware.PinDealer(list(ROOMS))
        dealer._return_class = hardware.Pin
        mapping = {room: room for room in ROOMS}
        cleanup = lambda: None
    elif device.lower() in ('rpi', 'raspberry', 'raspberrypi'):
        import raspberrypi
        dealer = raspberrypi.PinDealer([7, 8])
        mapping = {'living': 7, 'bedroom': 8}
        cleanup = lambda: raspberrypi.GPIO.cleanup([7, 8])
    else:
        import arduino
        mapping = {'living': ('0', '1'), 'bedroom': ('c', 'o')}
        dealer = arduino.PinDealer(list(mapping.values()), device)
        cleanup = dealer.get_ser().close
    pins = {}
    try:
        for room, number in mapping.items():
            pins[room] = dealer.get_pin(number)
        return LocalController(pins, cleanup)
    except Exception:
        for pin in pins.values():
            try:
                pin.disable()
            except Exception:
                pass
        cleanup()
        raise
