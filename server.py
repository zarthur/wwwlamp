"""Browser interface using either a local or remote lamp controller."""
import argparse
import json
import os

import cherrypy
from mako.lookup import TemplateLookup

from controller import ControllerError, ROOMS, create_controller
from remote_controller import RemoteController

ROOT = os.path.dirname(os.path.abspath(__file__))
lookup = TemplateLookup(directories=[os.path.join(ROOT, 'templates')])


class Control:
    def __init__(self, controller):
        self.controller = controller

    @cherrypy.expose
    def index(self, **kwargs):
        cherrypy.response.headers['Cache-Control'] = 'no-store'
        error = None
        if cherrypy.request.method == 'POST':
            updates = {}
            for field, value in kwargs.items():
                room = {'toggleswitch0': 'living', 'toggleswitch1': 'bedroom'}.get(field)
                if room is None or value not in ('on', 'off'):
                    raise cherrypy.HTTPError(400, 'Invalid lamp update')
                updates[room] = value == 'on'
            if not updates:
                raise cherrypy.HTTPError(400, 'Expected a lamp update')
            try:
                states = self.controller.set_states(updates)
            except ControllerError:
                raise cherrypy.HTTPError(503, 'Hardware unavailable; refresh state before retrying')
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return json.dumps({'states': states}).encode('utf-8')
        if cherrypy.request.method != 'GET':
            raise cherrypy.HTTPError(405)
        try:
            states = self.controller.get_states()
        except ControllerError:
            states = {room: None for room in ROOMS}
            error = 'Hardware unavailable. Refresh status to reconnect.'
        return lookup.get_template('index.html').render(states=states, error=error)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def status(self):
        cherrypy.response.headers['Cache-Control'] = 'no-store'
        if cherrypy.request.method != 'GET':
            raise cherrypy.HTTPError(405)
        try:
            return {'states': self.controller.get_states()}
        except ControllerError:
            raise cherrypy.HTTPError(503, 'Hardware unavailable')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('device', nargs='?', default='debug', help='debug, RPi, or Arduino serial path (local mode)')
    parser.add_argument('ipaddr', nargs='?', default='127.0.0.1')
    parser.add_argument('ipport', nargs='?', type=int, default=8080)
    parser.add_argument('--hardware-url')
    parser.add_argument('--timeout', type=float, default=3)
    args = parser.parse_args()
    if args.hardware_url:
        try:
            controller = RemoteController(args.hardware_url, os.environ.get('WWWLAMP_HARDWARE_TOKEN'), args.timeout)
        except ValueError as exc:
            parser.error(str(exc))
    else:
        controller = create_controller(args.device)
    cherrypy.config.update({'server.socket_host': args.ipaddr,
                           'server.socket_port': args.ipport,
                           'engine.autoreload.on': False})
    cherrypy.engine.subscribe('stop', controller.close)
    cherrypy.quickstart(Control(controller), '/', config={
        '/public': {'tools.staticdir.on': True,
                    'tools.staticdir.dir': os.path.join(ROOT, 'templates/public')}})


if __name__ == '__main__':
    main()
