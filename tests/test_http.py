import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pytest

from controller import ControllerError
from remote_controller import RemoteController

ROOT = Path(__file__).resolve().parents[1]
TOKEN = 'integration-test-token'


def port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def request(url, data=None, token=None, method=None, content_type='application/json'):
    headers = {'Content-Type': content_type}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=3) as response:
            return response.status, response.read()
    except HTTPError as response:
        return response.code, response.read()


@contextmanager
def process(script, args, url, tmp_path):
    with (tmp_path / (script + '.log')).open('a') as log:
        proc = subprocess.Popen([sys.executable, str(ROOT / script)] + args,
                                cwd=str(tmp_path), stdout=log, stderr=log,
                                env=dict(os.environ, WWWLAMP_HARDWARE_TOKEN=TOKEN))
        try:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    pytest.fail((tmp_path / (script + '.log')).read_text())
                try:
                    request(url)
                    break
                except (URLError, OSError):
                    time.sleep(.05)
            else:
                pytest.fail('Server did not start')
            yield proc
        finally:
            if proc.poll() is None:
                proc.terminate()
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()


def test_two_process_operation_and_independent_restarts(tmp_path):
    hardware_port, web_port = port(), port()
    base = 'http://127.0.0.1:' + str(hardware_port)
    web = 'http://127.0.0.1:' + str(web_port)
    api = base + '/api/v1/states'
    hw_args = ['debug', '--port', str(hardware_port)]
    web_args = ['debug', '127.0.0.1', str(web_port), '--hardware-url', base, '--timeout', '.2']
    client = RemoteController(base, TOKEN)
    with process('hardware_server.py', hw_args, api, tmp_path) as hardware:
        assert request(api)[0] == 401
        assert request(api, token='wrong')[0] == 401
        assert request(api, token=TOKEN, method='DELETE')[0] == 405
        for body in (b'{', b'{}', b'{"living":1}', b'{"unknown":true}', b'[]'):
            status, body = request(api, body, TOKEN)
            assert status == 400
            assert 'error' in json.loads(body)
        assert request(api, b'living=true', TOKEN, content_type='text/plain')[0] == 415
        assert request(api, b' ' * 5000, TOKEN)[0] == 413
        assert client.get_states() == {'living': False, 'bedroom': False}
        with process('server.py', web_args, web, tmp_path):
            status, page = request(web)
            assert status == 200 and b'Lamps' in page
            assert request(web + '/public/css/default.css')[0] == 200
            status, body = request(web + '/index', b'toggleswitch0=on', content_type='application/x-www-form-urlencoded')
            assert status == 200
            assert json.loads(body)['states'] == {'living': True, 'bedroom': False}
            request(web + '/index?toggleswitch0=off')
            assert client.get_states()['living'] is True  # GET cannot mutate
            assert request(web + '/index', b'bad=on', content_type='application/x-www-form-urlencoded')[0] == 400
        # Restarting the web process leaves hardware untouched.
        assert client.get_states()['living'] is True
        with process('server.py', web_args, web, tmp_path):
            assert json.loads(request(web + '/status')[1])['states']['living'] is True
            hardware.terminate()
            hardware.wait(timeout=8)
            assert request(web + '/status')[0] == 503
            assert b'Hardware unavailable' in request(web)[1]
            assert request(web + '/index', b'toggleswitch0=off', content_type='application/x-www-form-urlencoded')[0] == 503
            with process('hardware_server.py', hw_args, api, tmp_path):
                assert json.loads(request(web + '/status')[1])['states'] == {'living': False, 'bedroom': False}


def test_local_debug_mode(tmp_path):
    web_port = port()
    web = 'http://127.0.0.1:' + str(web_port)
    with process('server.py', ['debug', '127.0.0.1', str(web_port)], web, tmp_path):
        assert request(web + '/index', b'toggleswitch1=on', content_type='application/x-www-form-urlencoded')[0] == 200
        assert json.loads(request(web + '/status')[1])['states'] == {'living': False, 'bedroom': True}


def test_remote_failure_validation_and_timeout_after_apply():
    state = {'living': False, 'bedroom': False}
    commands = []
    payload = [None]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_GET(self):
            body = payload[0] or json.dumps({'states': state}).encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body)
        def do_POST(self):
            updates = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            commands.append(updates)
            state.update(updates)
            time.sleep(.15)
            self.send_response(200)
            self.end_headers()
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    client = RemoteController('http://127.0.0.1:' + str(server.server_port), TOKEN, timeout=.05)
    try:
        with pytest.raises(ControllerError):
            client.set_states({'living': True})
        assert client.get_states()['living'] is True
        assert commands == [{'living': True}]  # No automatic replay.
        for body in (b'bad json', b'{}', b'null', b'{"states":{"living":1,"bedroom":false}}', b'x' * 65537):
            payload[0] = body
            with pytest.raises(ControllerError):
                client.get_states()
    finally:
        server.shutdown()
        server.server_close()
        worker.join()


def test_web_import_does_not_load_hardware_dependencies():
    subprocess.run([sys.executable, '-c',
                    'import server, sys; assert not any(x in sys.modules for x in ("serial", "RPi.GPIO", "arduino", "raspberrypi"))'],
                   cwd=str(ROOT), check=True)


@pytest.mark.parametrize('timeout', [0, -1, float('nan'), float('inf')])
def test_invalid_timeouts(timeout):
    with pytest.raises(ValueError):
        RemoteController('http://localhost:8081', TOKEN, timeout)


def test_redirect_is_not_followed():
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_GET(self):
            requests.append(self.path)
            self.send_response(302)
            self.send_header('Location', '/other')
            self.end_headers()
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        client = RemoteController('http://127.0.0.1:' + str(server.server_port), TOKEN)
        with pytest.raises(ControllerError):
            client.get_states()
        assert requests == ['/api/v1/states']
    finally:
        server.shutdown()
        server.server_close()
        worker.join()
