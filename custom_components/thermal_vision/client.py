"""Thermal Vision API client"""

import requests

from urllib.parse import urljoin


class ThermalVisionClient(object):
    def __init__(self, base_url, verify_ssl=False):
        self._timeout = 1
        self._base_url = base_url
        self._verify_ssl = verify_ssl

        self._pixels = None
        self._temp = None
        self._person_detected = None

    def call(self):
        response = requests.get(
            urljoin(self._base_url, "raw"),
            stream=True,
            timeout=self._timeout,
            verify=self._verify_ssl,
        )
        response.raise_for_status()
        decoded = response.json()

        if "temp" in decoded:
            self._temp = decoded["temp"]
        else:
            self._temp = None

        if "person_detected" in decoded:
            self._person_detected = decoded["person_detected"]
        else:
            self._person_detected = None

        self._pixels = list(map(lambda x: float(x), decoded["data"].split(",")))

    def get_temp(self):
        return self._temp

    def get_raw(self):
        return self._pixels

    def get_person_detected(self):
        return self._person_detected
