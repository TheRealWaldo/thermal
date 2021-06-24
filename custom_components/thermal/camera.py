"""Thermal Grid Camera"""

import logging
import asyncio
import aiohttp
import async_timeout

import io
import time

import numpy as np
import voluptuous as vol

from colour import Color
from PIL import Image, ImageDraw

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from homeassistant.components.camera import PLATFORM_SCHEMA, Camera
from homeassistant.helpers import config_validation as cv

from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_VERIFY_SSL,
)

from .utils import constrain, map_value
from .interpolate import interpolate
from urllib.parse import urljoin
from .client import Client

from .const import (
    SESSION_TIMEOUT,
    CONF_WIDTH,
    CONF_HEIGHT,
    CONF_METHOD,
    CONF_AUTO_RANGE,
    CONF_MIN_TEMPERATURE,
    CONF_MAX_TEMPERATURE,
    CONF_ROTATE,
    CONF_MIRROR,
    CONF_FORMAT,
    CONF_COLD_COLOR,
    CONF_HOT_COLOR,
    CONF_SENSOR,
    CONF_INTERPOLATE,
    CONF_ROWS,
    CONF_COLS,
    DEFAULT_NAME,
    DEFAULT_VERIFY_SSL,
    DEFAULT_IMAGE_WIDTH,
    DEFAULT_IMAGE_HEIGHT,
    DEFAULT_METHOD,
    DEFAULT_MIN_TEMPERATURE,
    DEFAULT_MAX_TEMPERATURE,
    DEFAULT_ROTATE,
    DEFAULT_MIRROR,
    DEFAULT_FORMAT,
    DEFAULT_ROWS,
    DEFAULT_COLS,
    DEFAULT_COLD_COLOR,
    DEFAULT_HOT_COLOR,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.url,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): cv.boolean,
        vol.Optional(CONF_WIDTH, default=DEFAULT_IMAGE_WIDTH): cv.positive_int,
        vol.Optional(CONF_HEIGHT, default=DEFAULT_IMAGE_HEIGHT): cv.positive_int,
        vol.Optional(CONF_AUTO_RANGE, default=False): cv.boolean,
        vol.Optional(CONF_MIN_TEMPERATURE, default=DEFAULT_MIN_TEMPERATURE): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=100), msg="invalid min temperature"
        ),
        vol.Optional(CONF_MAX_TEMPERATURE, default=DEFAULT_MAX_TEMPERATURE): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=100), msg="invalid max temperature"
        ),
        vol.Optional(CONF_SENSOR): vol.Schema(
            {
                vol.Required(CONF_ROWS): cv.positive_int,
                vol.Required(CONF_COLS): cv.positive_int,
            }
        ),
        vol.Optional(CONF_INTERPOLATE): vol.Schema(
            {
                vol.Optional(CONF_ROWS): cv.positive_int,
                vol.Optional(CONF_COLS): cv.positive_int,
                vol.Optional(CONF_METHOD, default=DEFAULT_METHOD): cv.string,
            }
        ),
        vol.Optional(CONF_FORMAT, default=DEFAULT_FORMAT): cv.string,
        vol.Optional(CONF_MIRROR, default=DEFAULT_MIRROR): cv.boolean,
        vol.Optional(CONF_ROTATE, default=DEFAULT_ROTATE): cv.positive_int,
        vol.Optional(CONF_COLD_COLOR, default=DEFAULT_COLD_COLOR): cv.string,
        vol.Optional(CONF_HOT_COLOR, default=DEFAULT_HOT_COLOR): cv.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up camera component."""
    _LOGGER.debug("async setup Thermal camera")
    async_add_entities([ThermalCamera(config)])


class ThermalCamera(Camera):
    """A camera component producing thermal image from grid sensor data"""

    def __init__(self, config):
        """Initialize the component."""
        super().__init__()
        self._name = config.get(CONF_NAME)
        _LOGGER.debug(f"Initialize Thermal camera {self._name}")

        self._host = config.get(CONF_HOST)

        self._image_width = config.get(CONF_WIDTH)
        self._image_height = config.get(CONF_HEIGHT)
        self._min_temperature = config.get(CONF_MIN_TEMPERATURE)
        self._max_temperature = config.get(CONF_MAX_TEMPERATURE)
        self._color_depth = 1024
        self._rotate = config.get(CONF_ROTATE)
        self._mirror = config.get(CONF_MIRROR)
        self._format = config.get(CONF_FORMAT)

        sensor = config.get(
            CONF_SENSOR, {CONF_ROWS: DEFAULT_ROWS, CONF_COLS: DEFAULT_COLS}
        )
        self._rows = sensor.get(CONF_ROWS, DEFAULT_ROWS)
        self._cols = sensor.get(CONF_COLS, DEFAULT_COLS)

        interpolate = config.get(
            CONF_INTERPOLATE,
            {CONF_ROWS: 32, CONF_COLS: 32, CONF_METHOD: DEFAULT_METHOD},
        )
        self._interpolate_rows = interpolate.get(CONF_ROWS, 32)
        self._interpolate_cols = interpolate.get(CONF_COLS, 32)
        self._method = interpolate.get(CONF_METHOD, DEFAULT_METHOD)

        self._auto_range = config.get(CONF_AUTO_RANGE)
        self._verify_ssl = config.get(CONF_VERIFY_SSL)

        color_cold = config.get(CONF_COLD_COLOR)
        color_hot = config.get(CONF_HOT_COLOR)
        self._colors = list(
            Color(color_cold).range_to(Color(color_hot), self._color_depth)
        )
        self._colors = [
            (int(c.red * 255), int(c.green * 255), int(c.blue * 255))
            for c in self._colors
        ]

        self._attributes = {}
        self._setup_default_image()

    @property
    def name(self):
        """Return the component name."""
        return self._name

    @property
    def should_poll(self):
        """No need to poll cameras."""
        return False

    @property
    def device_state_attributes(self):
        """Return the camera state attributes."""
        return self._attributes

    async def async_camera_image(self):
        """Pull image from camera"""
        websession = async_get_clientsession(self.hass, verify_ssl=self._verify_ssl)
        try:
            with async_timeout.timeout(SESSION_TIMEOUT):
                start = int(round(time.time() * 1000))
                response = await websession.get(urljoin(self._host, "raw"))
                jsonResponse = await response.json()
                data = jsonResponse["data"].split(",")
                self._setup_range(data)
                image = self._camera_image(data)
                # Approx frame rate
                fps = int(1000.0 / (int(round(time.time() * 1000)) - start))
                self._attributes = {
                    "fps": fps,
                    "min": self._min_temperature,
                    "max": self._max_temperature,
                }
                return image
        except asyncio.TimeoutError:
            _LOGGER.warning("Timeout getting camera image from %s", self._name)
            return self._default_image
        except aiohttp.ClientError as err:
            _LOGGER.error("Error getting new camera image from %s: %s", self._name, err)
        except Exception as err:
            _LOGGER.error("Failed to generate camera %s", err)

    def camera_image(self):
        client = Client(self._host, self._verify_ssl)
        return self._camera_image(client.get_raw())

    def _setup_range(self, pixels):
        if self._auto_range:
            min_temp = float(min(pixels))
            max_temp = float(max(pixels))
            _LOGGER.debug("Minimum temperature %s", min_temp)
            _LOGGER.debug("Maximum temperature %s", max_temp)
            if (
                min_temp != max_temp
                and max_temp > min_temp
                and not (
                    min_temp == self._min_temperature
                    and max_temp == self._max_temperature
                )
            ):
                self._min_temperature = min_temp
                self._max_temperature = max_temp
                self._setup_default_image()

    def _setup_default_image(self):
        self._default_image = self._camera_image(
            np.full(self._rows * self._cols, self._min_temperature)
        )

    def _camera_image(self, pixels):
        """Create image from thermal camera pixels (temperatures)"""
        # Map to colors depth range
        pixels = [
            map_value(
                p,
                self._min_temperature,
                self._max_temperature,
                0,
                self._color_depth - 1,
            )
            for p in pixels
        ]
        # Convert to 2D
        pixels = np.reshape(pixels, (self._rows, self._cols))
        # Rotate (flip)
        if self._rotate == 180:
            pixels = np.flip(pixels, 0)
        # Mirror
        if self._mirror:
            pixels = np.flip(pixels, 1)
        # Input / output grid
        xi = np.linspace(0, self._cols - 1, self._cols)
        yi = np.linspace(0, self._rows - 1, self._rows)
        xo = np.linspace(0, self._cols - 1, self._interpolate_cols)
        yo = np.linspace(0, self._rows - 1, self._interpolate_rows)
        # Interpolate
        interpolation = interpolate(xi, yi, pixels, xo, yo, self._method)
        # Draw surface
        image = Image.new("RGB", (self._image_width, self._image_height))
        draw = ImageDraw.Draw(image)
        # Pixel size
        pixel_width = self._image_width / self._interpolate_cols
        pixel_height = self._image_height / self._interpolate_rows
        # Draw intepolated image
        for y, row in enumerate(interpolation):
            for x, pixel in enumerate(row):
                color_index = constrain(int(pixel), 0, self._color_depth - 1)
                x0 = pixel_width * x
                y0 = pixel_height * y
                x1 = x0 + pixel_width
                y1 = y0 + pixel_height
                draw.rectangle(((x0, y0), (x1, y1)), fill=self._colors[color_index])
        # Return image
        with io.BytesIO() as output:
            if self._format is "jpeg":
                image.save(
                    output,
                    format=self._format,
                    quality=80,
                    optimize=True,
                    progressive=True,
                )
            else:
                image.save(output, format=self._format)
            return output.getvalue()
