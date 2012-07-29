import cherrypy
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
            self.ser = serial.Serial(port, 9600)
        except:
            print("Invalid device")
            sys.exit()

    @cherrypy.expose
    def index(self):
        """index.html page for site"""
        return render('index.html')

    @cherrypy.expose
    def switch0(self, *args, **kwargs):
        """Toggle first relay"""
        self.ser.write('0'.encode())
        return render('index.html')

    @cherrypy.expose
    def switch1(self, *args, **kwargs):
        """Toggle second relay"""
        self.ser.write('1'.encode())
        return render('index.html')

    @cherrypy.expose
    def switch_all(self, *args, **kwargs):
        """Toggle both relays"""
        self.ser.write('0'.encode())
        self.ser.write('1'.encode())
        return render('index.html')

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
