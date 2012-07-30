import cherrypy
import io
import os
import serial
import sys

from mako.template import Template
from mako.lookup import TemplateLookup

lookup = TemplateLookup(directories=['templates'])

def render(*args, **kwargs):
    """shortcut render function for use with mako"""
    page = args[0]
    tmpl = lookup.get_template(page)
    return tmpl.render(**kwargs)

class Control(object):
    """Class defining structure of website and providing
    methods to control relays via a serial port
    """
    def __init__(self, port):
        try:
            self.ser = serial.Serial(port, 9600) if port != 'DEBUG' \
                        else io.StringIO('')
        except:
            print("Invalid device")
            sys.exit()

        self._debug = True if port == 'DEBUG' else False
        
        self.board_states = {'bedroom': False, 'living': False}
        self.web_states = {'bedroom': False, 'living': False}

    @cherrypy.expose
    def index(self):
        """index.html page for site"""
        return render('index.html', states=self.web_states)

    @cherrypy.expose
    def toggle(self, *args, **kwargs):
        living = kwargs.get('checkbox1', '')
        bedroom = kwargs.get('checkbox2', '')
        
        self.web_states['living'] = True if living.lower() == 'true' else False
        self.web_states['bedroom'] = True if bedroom.lower() == 'true' else False
        
        if self.board_states['living'] != self.web_states['living']:
            if not self._debug:
                self.ser.write('0'.encode())
            self.board_states['living'] = self.web_states['living']

        if self.board_states['bedroom'] != self.web_states['bedroom']:
            if not self._debug:
                self.ser.write('1'.encode())
            self.board_states['bedroom'] = self.web_states['bedroom']

        return render('index.html', states=self.web_states)

def main(port, ip_addr):
    """start the server"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cherrypy.config.update({'server.socket_host': ip_addr,
                            'server.socket_port': 8080})
    conf = {'/public': {'tools.staticdir.on': True,
                        'tools.staticdir.dir': os.path.join(current_dir, 'templates/public')}}
    cherrypy.quickstart(Control(port), '/' , config=conf)


if __name__ == '__main__':
    port = sys.argv[1]
    ip_addr = sys.argv[2]
    main(port, ip_addr)
