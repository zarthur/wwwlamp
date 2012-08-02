wwwlamp
=======
Control lamps (and other things) from a browser.

Required Software
-----------------
- Python 3
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
This can be changed by modifying relay_control.ino
- Power 5V connected to Relay VCC
- Digital GND connected to Relay GND
- Digital 3 connected to Relay 1 IN
- Digital 5 connected to Relay 2 IN

Files
-----
- server.py - Python file to connect to Arduino and setup webserver
- hardware.py - Generic hardware controller, hardware controllers should inherit from this
- arduino.py - Pin/hardware controller for Arduino
- raspberrypi.py - Pin/hardware controller for RaspberryPi's GPIO
- relay_control.ino - Code to control a relay from the Arduino board.
- templates/ - Files for website




