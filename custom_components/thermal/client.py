"""Thermal sensor API client"""

import logging
import requests

from urllib.parse import urljoin

class Client(object):

    def __init__(self, base_url, username = None, password = None, verify_ssl = False):
        self._timeout = 1
        self._base_url = base_url
        self._verify_ssl = verify_ssl
        if username and password:
            if self._authentication == HTTP_DIGEST_AUTHENTICATION:
                self._auth = HTTPDigestAuth(username, password)
            else:
                self._auth = HTTPBasicAuth(username, password)
        else:
          self._auth = None

    def get_raw(self):
        req_url = urljoin(self._base_url, 'raw')
        if self._auth:
            response = requests.get(req_url, auth=auth, stream=True, timeout=self._timeout, verify=self._verify_ssl)
        else:
            response = requests.get(req_url, stream=True, timeout=self._timeout)
        response.raise_for_status()
        return list(map(lambda x: float(x), response.json()['data'].split(',')))