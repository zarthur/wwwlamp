"""HTTP client implementing the same interface as LocalController."""
import json
import math
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

from controller import ControllerError, validate_states, validate_updates


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class RemoteController:
    def __init__(self, url, token, timeout=3):
        parsed = urlsplit(url)
        if (parsed.scheme not in ('http', 'https') or not parsed.hostname
                or parsed.username or parsed.password or parsed.query or parsed.fragment):
            raise ValueError('Expected an HTTP(S) hardware service URL')
        if not token or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError('A token and positive timeout are required')
        self._url = url.rstrip('/') + '/api/v1/states'
        self._token = token
        self._timeout = timeout
        self._opener = build_opener(NoRedirect())

    def _request(self, updates=None):
        data = None if updates is None else json.dumps(updates).encode('utf-8')
        request = Request(self._url, data=data, headers={
            'Authorization': 'Bearer ' + self._token,
            'Content-Type': 'application/json', 'Accept': 'application/json'})
        try:
            with self._opener.open(request, timeout=self._timeout) as response:
                body = response.read(65537)
                if len(body) > 65536:
                    raise ValueError('Oversized controller response')
                return validate_states(json.loads(body)['states'])
        except (HTTPError, URLError, HTTPException, OSError, ValueError, KeyError, TypeError) as exc:
            # Never replay a command automatically: its outcome may be unknown.
            raise ControllerError('Hardware service unavailable or returned an invalid response') from exc

    def get_states(self):
        return self._request()

    def set_states(self, updates):
        return self._request(validate_updates(updates))

    def close(self):
        """Closing a web client must not change hardware state."""
