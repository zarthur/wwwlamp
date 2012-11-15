"""Webserver for site allowing control over hardware"""

import argparse
import os

import cherrypy

from mako.lookup import TemplateLookup

lookup = TemplateLookup(directories=['templates'])


def import_rasperrypi():
    """Import RaspberryPi hardware module"""
    import raspberrypi as hardware
    available_pins = [7, 8]
    return hardware, available_pins


def import_arduino():
    """Import Arduino hardware module"""
    import arduino as hardware
    available_pins = [('0', '1'), ('o', 'c')]
    return hardware, available_pins


def render(*args, **kwargs):
    """shortcut render function for use with mako"""
    page = args[0]
    tmpl = lookup.get_template(page)
    return tmpl.render(**kwargs)


class Control(object):
    """Class defining structure of website and providing
    methods to control relays via a serial port
    """
    def __init__(self, hardware, available_pins, port=None):
        self._debug = True if available_pins == 'DEBUG' else False
        if not self._debug:
            self._pin_dealer = hardware.PinDealer(available_pins, port)
            self._bedroom_pin = self._pin_dealer.get_pin()
            self._living_pin = self._pin_dealer.get_pin()

        self.board_states = {'bedroom': False, 'living': False}
        self.web_states = {'bedroom': False, 'living': False}

    @cherrypy.expose
    def index(self, *args, **kwargs):
        """index for site"""
        cherrypy.response.headers['Cache-Control'] = "no-cache"
        if kwargs:
            switch0 = kwargs.get('toggleswitch0', 'off')
            switch1 = kwargs.get('toggleswitch1', 'off')

            self.web_states['living'] = True if switch0 == 'on' else False
            self.web_states['bedroom'] = True if switch1 == 'on' else False

            if self.board_states['living'] != self.web_states['living']:
                if not self._debug:
                    self._living_pin.toggle()
                else:
                    print('Switching living')

                self.board_states['living'] = self.web_states['living']

            if self.board_states['bedroom'] != self.web_states['bedroom']:
                if not self._debug:
                    self._bedroom_pin.toggle()
                else:
                    print('Switching bedroom')

                self.board_states['bedroom'] = self.web_states['bedroom']

        return render('index.html', states=self.web_states)

    @cherrypy.expose
    def status(self):
        return render('status.html', status=self.board_states)


def main(hardware, available_pins, port, ip_addr, ip_port=8080):
    """start the server"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cherrypy.config.update({'server.socket_host': ip_addr,
                            'server.socket_port': ip_port})
    conf = {'/public': {'tools.staticdir.on': True,
                        'tools.staticdir.dir': os.path.join(current_dir,
                                                'templates/public')}}
    cherrypy.quickstart(Control(hardware, available_pins, port), '/',
                        config=conf)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start wwwlamp server')
    parser.add_argument('device',
                        help='port of device to use; for Arduino use '
                            '"/dev/ttyACM0", for RaspberryPi, use "RPi"',
                        default='RPi')

    parser.add_argument('ipaddr', help='ip address to bind to')
    parser.add_argument('ipport', help='port of specified address to use',
                        default=8080)

    args = parser.parse_args()

    if args.device.lower() in ['rpi', 'raspberry', 'raspberrypi']:
        hardware, pins = import_rasperrypi()
        port = None
    elif args.device.lower() == 'debug':
        hardware, pins = None, 'DEBUG'
        port = None
    else:
        hardware, pins = import_arduino()
        port = args.device

    main(hardware, pins, port, args.ipaddr, int(args.ipport))
