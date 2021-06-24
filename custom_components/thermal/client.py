"""Thermal sensor API client"""

import requests

from urllib.parse import urljoin


class Client(object):
    def __init__(self, base_url, verify_ssl=False):
        self._timeout = 1
        self._base_url = base_url
        self._verify_ssl = verify_ssl

    def get_raw(self):
        response = requests.get(
            urljoin(self._base_url, "raw"),
            stream=True,
            timeout=self._timeout,
            verify=self._verify_ssl,
        )
        response.raise_for_status()
        return list(map(lambda x: float(x), response.json()["data"].split(",")))
