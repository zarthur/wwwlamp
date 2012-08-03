import cherrypy
import io
import os
import serial
import sys

from mako.template import Template
from mako.lookup import TemplateLookup

lookup = TemplateLookup(directories=['templates'])

def import_rasperrypi():
    import raspberrypi as hardware
    available_pins = [7, 8]
    return available_pins

def import_arduino():
    import arduino as hardware
    available_pins = [('0', '1'), ('o', 'c')] 
    return available_pins

def render(*args, **kwargs):
    """shortcut render function for use with mako"""
    page = args[0]
    tmpl = lookup.get_template(page)
    return tmpl.render(**kwargs)

class Control(object):
    """Class defining structure of website and providing
    methods to control relays via a serial port
    """
    def __init__(self, available_pins):
        self._debug = True if available_pins == 'DEBUG' else False
        if not self._debug:
            self._pin_dealer = hardware.PinDealer(available_pins)
            self._bedroom_pin = self._pin_dealer.get_pin()
            self._living_pin = self._pin_dealer.get_pin()
        
        self.board_states = {'bedroom': False, 'living': False}
        self.web_states = {'bedroom': False, 'living': False}

    @cherrypy.expose
    def index(self, *args, **kwargs):
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

def main(port, ip_addr, ip_port=8080):
    """start the server"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cherrypy.config.update({'server.socket_host': ip_addr,
                            'server.socket_port': ip_port})
    conf = {'/public': {'tools.staticdir.on': True,
                        'tools.staticdir.dir': os.path.join(current_dir, 'templates/public')}}
    cherrypy.quickstart(Control(port), '/' , config=conf)


if __name__ == '__main__':
    port = sys.argv[1]
    ip_addr = sys.argv[2]
    main(port, ip_addr)
