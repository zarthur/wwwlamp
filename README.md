wwwlamp
===============

Control lamps (and other things) from a browser.

Required Software:
    Python 3
    CherryPy
    Mako
    PySerial

Additional Hardware:
    Arduino
    Relays

Arduino Pin Configuration:
    Power 5V connected to Relay VCC
    Digital GND connected to Relay GND
    Digital 3 connected to Relay 1 IN
    Digital 5 connected to Relay 2 IN

Files:
    server.py - Python file to connect to Arduino and setup webserver
    relay_control.ino - Modified version of Maurice Ribble's code
        to control a relay from the Arduino board.  Original code at
        http://www.glacialwanderer.com/_blog/blog2008/04_April/relay.pde
    templates/ - Files for website




