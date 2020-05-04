"""Thermal Grid Camera"""

import logging
import asyncio

import numpy as np

import aiohttp
import async_timeout
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from urllib.parse import urljoin

import voluptuous as vol

from homeassistant.helpers.aiohttp_client import (
    async_get_clientsession
)

from homeassistant.components.camera import PLATFORM_SCHEMA, Camera
from homeassistant.helpers import config_validation as cv
# from homeassistant.util import Throttle

from homeassistant.const import (
  CONF_AUTHENTICATION,
  CONF_HOST,
  CONF_NAME,
  CONF_PASSWORD,
  CONF_USERNAME,
  CONF_VERIFY_SSL,
  HTTP_BASIC_AUTHENTICATION,
  HTTP_DIGEST_AUTHENTICATION
)

from .utils import interpolate_image

from .const import (
  SESSION_TIMEOUT,
  CONF_WIDTH, CONF_HEIGHT, CONF_METHOD,
  CONF_MIN_TEMPERATURE, CONF_MAX_TEMPERATURE,
  CONF_ROTATE, CONF_MIRROR,
  CONF_SENSOR, CONF_ROWS, CONF_COLS,
  DEFAULT_NAME, DEFAULT_VERIFY_SSL, DEFAULT_IMAGE_WIDTH, DEFAULT_IMAGE_HEIGHT, DEFAULT_METHOD,
  DEFAULT_MIN_TEMPERATURE, DEFAULT_MAX_TEMPERATURE,
  DEFAULT_ROTATE, DEFAULT_MIRROR,
  DEFAULT_ROWS, DEFAULT_COLS,
  DEFAULT_COLD_COLOR, DEFAULT_HOT_COLOR
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.url,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): cv.boolean,
    vol.Optional(CONF_WIDTH, default=DEFAULT_IMAGE_WIDTH): cv.positive_int,
    vol.Optional(CONF_HEIGHT, default=DEFAULT_IMAGE_HEIGHT): cv.positive_int,
    vol.Optional(CONF_MIN_TEMPERATURE, default=DEFAULT_MIN_TEMPERATURE): vol.All(
        vol.Coerce(float), vol.Range(min=0, max=100), msg="invalid min temperature"
    ),
    vol.Optional(CONF_MAX_TEMPERATURE, default=DEFAULT_MAX_TEMPERATURE): vol.All(
        vol.Coerce(float), vol.Range(min=0, max=100), msg="invalid max temperature"
    ),
    vol.Optional(CONF_SENSOR): vol.Schema({
        vol.Required(CONF_ROWS): cv.positive_int,
        vol.Required(CONF_COLS): cv.positive_int,
        }),
    vol.Optional(CONF_METHOD, default=DEFAULT_METHOD): cv.string,
    vol.Optional(CONF_MIRROR, default=DEFAULT_MIRROR): cv.boolean,
    vol.Optional(CONF_ROTATE, default=DEFAULT_ROTATE): cv.positive_int,
})


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up camera component."""
    async_add_entities([ThermalCamera(config)])


class ThermalCamera(Camera):
    """A camera component producing thermal image from grid sensor data"""

    def __init__(self, device_info):
        """Initialize the component."""
        super().__init__()
        self._name = device_info.get(CONF_NAME)
        _LOGGER.debug(f"Initialize Thermal camera {self._name}")

        self._host = device_info.get(CONF_HOST)
        
        self._image_width = device_info.get(CONF_WIDTH)
        self._image_height = device_info.get(CONF_HEIGHT)
        self._min_temperature = device_info.get(CONF_MIN_TEMPERATURE)
        self._max_temperature = device_info.get(CONF_MAX_TEMPERATURE)
        self._color_depth = 1024
        self._method = device_info.get(CONF_METHOD)
        self._color_cold = DEFAULT_COLD_COLOR
        self._color_hot = DEFAULT_HOT_COLOR
        self._rows = DEFAULT_ROWS
        self._cols = DEFAULT_COLS
        self._rotate = device_info.get(CONF_ROTATE)
        self._mirror = device_info.get(CONF_MIRROR)

        self._username = device_info.get(CONF_USERNAME)
        self._password = device_info.get(CONF_PASSWORD)
        self._authentication = device_info.get(CONF_AUTHENTICATION)        
        self._auth = None
        if self._username and self._password:
            if self._authentication == HTTP_BASIC_AUTHENTICATION:
                self._auth = aiohttp.BasicAuth(self._username, password=self._password)
        self._verify_ssl = device_info.get(CONF_VERIFY_SSL)

    @property
    def name(self):
        """Return the component name."""
        return self._name

    @property
    def should_poll(self):
        return True

    async def async_camera_image(self):
        """Pull image from camera"""
        websession = async_get_clientsession(self.hass, verify_ssl=self._verify_ssl)
        try:
            with async_timeout.timeout(SESSION_TIMEOUT):
                # Get pixels
                req_url = urljoin(self._host, 'raw')
                response = await websession.get(req_url, auth=self._auth)
                jsonResponse = await response.json()
                # Convert to 2D
                pixels = np.reshape(jsonResponse['data'].split(','), (self._rows, self._cols))
                # Generate JPEG image
                return interpolate_image(pixels, self._image_width, self._image_height,
                    self._min_temperature, self._max_temperature, self._color_cold, self._color_hot,
                    self._color_depth, self._method, self._rotate, self._mirror, "JPEG")
        except Exception as err:
            print(err)
            _LOGGER.error("Failed to connect to camera")