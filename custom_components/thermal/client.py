"""Thermal sensor API client"""

import requests


class Client(object):
    def __init__(self, base_url, username=None, password=None, verify_ssl=False):
        self._timeout = 1
        self._base_url = base_url

    def get_raw(self):
        response = requests.get(self._base_url, stream=True, timeout=self._timeout)
        response.raise_for_status()
        return list(map(lambda x: float(x), response.json()["data"].split(",")))
