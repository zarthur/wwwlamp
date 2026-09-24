import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from controller import ControllerError, LocalController, create_controller
from hardware import Pin, PinDealer


def test_explicit_commands_and_validation():
    controller = create_controller('debug')
    assert controller.set_states({'living': True}) == {'living': True, 'bedroom': False}
    assert controller.set_states({'living': True})['living'] is True
    for updates in ({}, {'living': 1}, {'unknown': True}, {'living': True, 'bedroom': 'off'}):
        with pytest.raises(ValueError):
            controller.set_states(updates)
    assert controller.get_states() == {'living': True, 'bedroom': False}
    snapshot = controller.get_states()
    snapshot['living'] = False
    assert controller.get_states()['living'] is True
    controller.close()
    controller.close()
    with pytest.raises(ControllerError):
        controller.set_states({'living': False})


def test_failure_records_partial_state_and_cleanup_continues():
    class FailingPin:
        def enable(self):
            raise OSError('Disconnected')
        disable = enable
    good = Pin('living', None)
    cleaned = []
    controller = LocalController({'living': good, 'bedroom': FailingPin()}, lambda: cleaned.append(True))
    with pytest.raises(ControllerError):
        controller.set_states({'living': True, 'bedroom': True})
    assert controller.get_states() == {'living': True, 'bedroom': None}
    controller.close()
    assert not good.is_enabled()
    assert cleaned == [True]


def test_commands_are_serialized():
    active = threading.Lock()
    overlaps = []
    class SlowPin:
        def enable(self):
            acquired = active.acquire(blocking=False)
            if not acquired:
                overlaps.append(True)
            time.sleep(.005)
            if acquired:
                active.release()
        disable = enable
    controller = LocalController({'living': SlowPin(), 'bedroom': SlowPin()})
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda n: controller.set_states({'living': bool(n % 2)}), range(30)))
    assert not overlaps


def test_arduino_mapping_and_cleanup(monkeypatch):
    writes = []
    class Serial:
        def __init__(self, port, baud, write_timeout):
            assert (port, baud, write_timeout) == ('fake-port', 9600, 3)
        def write(self, data):
            writes.append(data)
            return len(data)
        def close(self):
            writes.append('closed')
    monkeypatch.setitem(sys.modules, 'serial', SimpleNamespace(Serial=Serial))
    sys.modules.pop('arduino', None)
    controller = create_controller('fake-port')
    assert writes == [b'0', b'c']
    controller.set_states({'living': True, 'bedroom': True})
    assert writes[-2:] == [b'1', b'o']
    controller.close()
    assert writes[-3:] == [b'0', b'c', 'closed']


def test_gpio_mapping(monkeypatch):
    outputs = []
    gpio = SimpleNamespace(BCM=11, OUT=0, setmode=lambda mode: None,
                           setup=lambda pin, mode: None,
                           output=lambda pin, state: outputs.append((pin, state)),
                           cleanup=lambda pins: outputs.append(tuple(pins)))
    monkeypatch.setitem(sys.modules, 'RPi', SimpleNamespace(GPIO=gpio))
    monkeypatch.setitem(sys.modules, 'RPi.GPIO', gpio)
    sys.modules.pop('raspberrypi', None)
    controller = create_controller('RPi')
    controller.set_states({'living': True, 'bedroom': True})
    assert outputs[-2:] == [(7, True), (8, True)]
    controller.close()
    assert outputs[-1] == (7, 8)


def test_pin_close_returns_disabled_pin():
    dealer = PinDealer([7])
    dealer._return_class = Pin
    pin = dealer.get_pin()
    pin.enable()
    pin.close()
    assert dealer._available == [7]

    pin.close()
    with pytest.raises(RuntimeError):
        pin.enable()
