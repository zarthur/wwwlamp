wwwlamp
=======
Control lamps (and other things) from a browser.

Required Software
-----------------
- Python 3.14 (recommended; Python 3.12 is also tested)
- CherryPy
- Mako
- PySerial (if using an Arduino)
- RPi.GPIO (if using a RaspberryPi)

Additional Hardware
-------------------
- Arduino or RaspberryPi
- Relays

Arduino Pin Configuration
-------------------------
This can be changed by modifying relay_controller.ino
- Power 5V connected to Relay VCC
- Digital GND connected to Relay GND
- Digital 3 connected to Relay 1 IN
- Digital 5 connected to Relay 2 IN

RaspberryPi Configuration
-------------------------
See http://elinux.org/RPi_Low-level_peripherals for
pin details.

Files
-----
- server.py - Browser interface with local or remote hardware control
- hardware.py - Generic hardware controller, hardware controllers should inherit from this
- arduino.py - Pin/hardware controller for Arduino
- raspberrypi.py - Pin/hardware controller for RaspberryPi's GPIO
- relay_controller.ino - Code to control a relay from the Arduino board.
- templates/ - Files for website




Running locally or on two machines
---------------------------------

Install the shared dependencies in a virtual environment using Python 3.14:

```sh
python3.14 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

The `.python-version` file selects Python 3.14 for tools that support it. Use the
latest available 3.14 patch release (3.14.7 as of September 24, 2026). CI tests
Python 3.12 and 3.14, including the separate-process integration suite. When
upgrading an existing installation, create a fresh virtual environment with
Python 3.14 and reinstall dependencies; an existing environment retains its
original interpreter.

Only the hardware-owning machine needs `pyserial` for Arduino or `RPi.GPIO`
for a compatible Raspberry Pi. The web-only machine needs neither. The
Arduino must already be running `relay_controller.ino`.

The original local commands remain supported:

```sh
python server.py debug 127.0.0.1 8080
python server.py RPi 127.0.0.1 8080
python server.py /dev/ttyACM0 127.0.0.1 8080
```

`debug` uses in-memory pins and never accesses hardware. With no arguments,
`server.py` starts local debug mode at `127.0.0.1:8080`.

For two-machine operation, choose a long random shared token and supply it as
`WWWLAMP_HARDWARE_TOKEN` in each service's environment. For example:

```sh
# Hardware machine; substitute its private network address.
export WWWLAMP_HARDWARE_TOKEN='replace-with-your-shared-token'
python hardware_server.py RPi --host 192.168.1.20 --port 8081
# Or use /dev/ttyACM0 for Arduino, or debug for a hardware-free trial.
```

```sh
# Web machine; the positional device is ignored when --hardware-url is set.
export WWWLAMP_HARDWARE_TOKEN='replace-with-your-shared-token'
python server.py debug 127.0.0.1 8080 --hardware-url http://192.168.1.20:8081
```

Open the web machine's port 8080 in a browser. Change its bind address if it
needs to accept LAN connections. Both services bind to loopback by default.
The hardware API requires its token even on loopback. Use a trusted private
network or HTTPS via a reverse proxy; plain HTTP does not encrypt the token.
Keep the browser interface on a trusted network or behind authenticated access;
it does not provide user authentication. Do not expose either service directly
to the public internet. Run exactly one hardware service per board.

Architecture and API
--------------------

`controller.py` owns pins and serializes commands. `hardware_server.py` exposes
that controller; `remote_controller.py` connects the web application to it.
The web server continues to serve the templates and static assets.

The hardware service accepts `Authorization: Bearer <token>` and exposes:

- `GET /api/v1/states`: returns `{"states":{"living":false,"bedroom":false}}`.
- `POST /api/v1/states`, with `Content-Type: application/json`: accepts a nonempty
  subset such as `{"living":true}` and returns both resulting states.

Commands set explicit on/off values and can be repeated without toggling.
Unknown rooms and non-boolean values are rejected before any writes. Invalid
requests return 400, missing/incorrect tokens 401, unsupported methods 405,
wrong content types 415, and hardware failures 503. Request bodies are limited
to 4 KiB. Hardware API errors have an `error` JSON field.

State describes the last successful command, not measured relay feedback.
The Arduino firmware does not acknowledge commands. A failed write marks that
room's state `null` (unknown). Multi-room updates are serialized but are not
atomic: successful earlier writes remain applied if a later write fails.

The remote client has a three-second timeout, configurable with `--timeout`.
It never automatically replays commands or follows redirects. After an uncertain
command outcome the browser fetches state, and displays Unknown if that read
also fails. Refresh status reconnects without replaying old commands. Browser
updates send only the changed room. `GET /status` on the web server returns the
same state envelope; 503 indicates that the hardware service cannot be reached.

Hardware startup initializes both outputs off. Restarting or stopping a remote
web server does not change them. Graceful shutdown of the hardware owner tries
to turn off every output, then closes serial or cleans up GPIO. Abrupt power
loss, process termination without cleanup, and disconnected hardware cannot
guarantee an off state. On hardware-service restart, outputs initialize off
again; states are not persisted. Shutdown of local web mode also shuts down
its hardware controller.

Assignments are living = BCM GPIO 7 / Arduino digital 3 and bedroom = BCM GPIO
8 / Arduino digital 5. Arduino commands are `0`/`1` for living off/on and `c`/`o`
for bedroom off/on, matching the firmware.

Testing
-------

```sh
pip install -r requirements-dev.txt
python -m pytest -q
```

Tests use fake GPIO/serial drivers and separate hardware/web processes; they
require no board. They cover explicit commands, validation, authentication,
concurrent access, partial failures, timeouts after command application,
service outages/recovery, and independent restarts. Before connecting real
loads, verify both room mappings and on/off polarity on each supported board,
then verify startup and graceful-shutdown behavior. Automated tests do not
replace these physical checks.

Dependency updates
------------------

The tested direct dependencies are CherryPy 18.10.0, Mako 1.4.3, and pytest
9.1.1. Requirements allow compatible releases within each major version.
Upgrade in a fresh virtual environment and run the integration tests before
replacing a working deployment:

```sh
python3.14 -m venv .venv-upgrade
. .venv-upgrade/bin/activate
python -m pip install --upgrade -r requirements-dev.txt
python -m pip check
python -m pytest -q
```

The browser interface uses native HTML, CSS, and browser APIs (including fetch
and AbortController), with no jQuery or jQuery Mobile dependency. Use a current
browser. After UI changes, check commands, unavailable state, and recovery in a
browser as well as running the Python tests. Board-specific libraries remain
optional and require physical smoke tests when upgraded.
