"""Private HTTP API owning a single hardware controller."""
import argparse
import hmac
import json
import os

import cherrypy

from controller import ControllerError, create_controller, validate_updates


def json_error(status, message, traceback, version):
    cherrypy.response.headers['Content-Type'] = 'application/json'
    return json.dumps({'error': message}).encode('utf-8')


class HardwareAPI:
    def __init__(self, controller, token):
        self.controller = controller
        self.token = token

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def states(self):
        cherrypy.response.headers['Cache-Control'] = 'no-store'
        supplied = cherrypy.request.headers.get('Authorization', '')
        if not hmac.compare_digest(supplied.encode(), ('Bearer ' + self.token).encode()):
            raise cherrypy.HTTPError(401, 'Invalid hardware service token')
        method = cherrypy.request.method
        try:
            if method == 'GET':
                return {'states': self.controller.get_states()}
            if method != 'POST':
                cherrypy.response.headers['Allow'] = 'GET, POST'
                raise cherrypy.HTTPError(405, 'Use GET or POST')
            if cherrypy.request.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                raise cherrypy.HTTPError(415, 'Expected application/json')
            try:
                updates = validate_updates(json.loads(cherrypy.request.body.read()))
            except (ValueError, UnicodeError):
                raise cherrypy.HTTPError(400, 'Expected room names with boolean values')
            return {'states': self.controller.set_states(updates)}
        except ControllerError:
            raise cherrypy.HTTPError(503, 'Hardware operation failed; read state before retrying')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('device', help='debug, RPi, or Arduino serial path')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8081)
    args = parser.parse_args()
    token = os.environ.get('WWWLAMP_HARDWARE_TOKEN')
    if not token:
        parser.error('Set WWWLAMP_HARDWARE_TOKEN')
    controller = create_controller(args.device)
    cherrypy.config.update({'server.socket_host': args.host,
                           'server.socket_port': args.port,
                           'server.max_request_body_size': 4096,
                           'engine.autoreload.on': False,
                           'error_page.default': json_error})
    cherrypy.engine.subscribe('stop', controller.close)
    cherrypy.quickstart(HardwareAPI(controller, token), '/api/v1')


if __name__ == '__main__':
    main()
