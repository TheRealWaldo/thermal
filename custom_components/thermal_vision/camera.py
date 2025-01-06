"""Thermal Vision Camera"""

import logging
import asyncio
import aiohttp
import async_timeout

import io
import time
import base64

import numpy as np
import voluptuous as vol

from colour import Color
from PIL import Image, ImageDraw

from homeassistant.util.unit_conversion import TemperatureConverter
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from homeassistant.components.camera import PLATFORM_SCHEMA, Camera
from homeassistant.helpers import config_validation as cv

from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_VERIFY_SSL,
    UnitOfTemperature,
    STATE_UNKNOWN,
    STATE_UNAVAILABLE,
)

from .utils import constrain, map_value
from .interpolate import interpolate
from urllib.parse import urljoin
from .client import ThermalVisionClient

from .const import (
    CONF_OVERLAY,
    CONF_SESSION_TIMEOUT,
    DEFAULT_OVERLAY,
    DEFAULT_SESSION_TIMEOUT,
    CONF_WIDTH,
    CONF_HEIGHT,
    CONF_PRESERVE_ASPECT_RATIO,
    CONF_METHOD,
    CONF_AUTO_RANGE,
    CONF_MIN_DIFFERANCE,
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
    CONF_PIXEL_SENSOR,
    DEFAULT_NAME,
    DEFAULT_VERIFY_SSL,
    DEFAULT_IMAGE_WIDTH,
    DEFAULT_IMAGE_HEIGHT,
    DEFAULT_PRESERVE_ASPECT_RATIO,
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
        vol.Exclusive(CONF_HOST, 1): cv.url,
        vol.Exclusive(CONF_PIXEL_SENSOR, 1): cv.entity_id,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): cv.boolean,
        vol.Optional(CONF_WIDTH, default=DEFAULT_IMAGE_WIDTH): cv.positive_int,
        vol.Optional(CONF_HEIGHT, default=DEFAULT_IMAGE_HEIGHT): cv.positive_int,
        vol.Optional(
            CONF_PRESERVE_ASPECT_RATIO, default=DEFAULT_PRESERVE_ASPECT_RATIO
        ): cv.boolean,
        vol.Optional(CONF_AUTO_RANGE, default=False): cv.boolean,
        vol.Optional(CONF_MIN_DIFFERANCE, default=4): cv.positive_int,
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
        vol.Optional(
            CONF_SESSION_TIMEOUT, default=DEFAULT_SESSION_TIMEOUT
        ): cv.positive_int,
        vol.Optional(CONF_OVERLAY, default=DEFAULT_OVERLAY): cv.boolean,
    },
    {
        vol.Required(vol.Any(CONF_HOST, CONF_PIXEL_SENSOR)),
    },
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up camera component."""
    _LOGGER.debug("async setup Thermal camera")
    async_add_entities([ThermalVisionCamera(config, hass)])


class ThermalVisionCamera(Camera):
    """A camera component producing thermal image from grid sensor data"""

    def __init__(self, config, hass):
        """Initialize the component."""
        super().__init__()
        self._name = config.get(CONF_NAME)
        _LOGGER.debug(f"Initialize Thermal camera {self._name}")

        self._host = config.get(CONF_HOST)
        self._pixel_sensor = config.get(CONF_PIXEL_SENSOR)

        self._image_width = config.get(CONF_WIDTH)
        self._image_height = config.get(CONF_HEIGHT)
        self._preserve_aspect_ratio = config.get(CONF_PRESERVE_ASPECT_RATIO)
        self._min_temperature = config.get(CONF_MIN_TEMPERATURE)
        self._max_temperature = config.get(CONF_MAX_TEMPERATURE)
        self._pixel_min_temp = self._min_temperature
        self._pixel_max_temp = self._min_temperature
        self._color_depth = 1024
        self._rotate = config.get(CONF_ROTATE)
        self._mirror = config.get(CONF_MIRROR)
        self._format = config.get(CONF_FORMAT)
        self._session_timeout = config.get(CONF_SESSION_TIMEOUT)
        self._overlay = config.get(CONF_OVERLAY)
        self._min_diff = config.get(CONF_MIN_DIFFERANCE)
        self._fps = None
        self._temperature_unit = hass.config.units.temperature_unit
        _LOGGER.debug("Temperature unit %s", self._temperature_unit)

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
        if self._host:
            self._client = ThermalVisionClient(self._host, self._verify_ssl)

        self._setup_default_image()

    @property
    def name(self):
        """Return the component name."""
        return self._name

    @property
    def should_poll(self):
        """Need to poll for attributes."""
        return True

    @property
    def extra_state_attributes(self):
        """Return the camera state attributes."""
        return {
            "fps": self._fps,
            "min": self._pixel_min_temp
            if self._temperature_unit == UnitOfTemperature.CELSIUS
            else TemperatureConverter.convert(
                self._pixel_min_temp, UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT
            ),
            "max": self._pixel_max_temp
            if self._temperature_unit == UnitOfTemperature.CELSIUS
            else TemperatureConverter.convert(
                self._pixel_max_temp, UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT
            ),
            "range_min": self._min_temperature
            if self._temperature_unit == UnitOfTemperature.CELSIUS
            else TemperatureConverter.convert(
                self._min_temperature, UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT
            ),
            "range_max": self._max_temperature
            if self._temperature_unit == UnitOfTemperature.CELSIUS
            else TemperatureConverter.convert(
                self._max_temperature, UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT
            ),
        }

    async def async_camera_image(self, width=None, height=None):
        """Pull image from camera"""
        self._set_size(width, height)
        if self._host:
            start = int(round(time.time() * 1000))
            websession = async_get_clientsession(self.hass, verify_ssl=self._verify_ssl)
            try:
                with async_timeout.timeout(self._session_timeout):
                    response = await websession.get(urljoin(self._host, "raw"))
                    jsonResponse = await response.json()
                    if jsonResponse:
                        data = jsonResponse["data"].split(",")
                        self._setup_range(data)
                        self._default_image = self._camera_image(data)

            except asyncio.TimeoutError:
                _LOGGER.warning("Timeout getting camera image from %s", self._name)
                return self._default_image

            except aiohttp.ClientError as err:
                _LOGGER.error(
                    "Error getting new camera image from %s: %s", self._name, err
                )
                return self._default_image

            except Exception as err:
                _LOGGER.error("Failed to generate camera (%s)", err)
                return self._default_image

            self._fps = int(1000.0 / (int(round(time.time() * 1000)) - start))
        else:
            self._update_pixel_sensor()

        return self._default_image

    def camera_image(self, width=None, height=None):
        """Get image for camera"""
        self._set_size(width, height)

        if self._host:
            self._client.call()
            return self._camera_image(self._client.get_raw())
        else:
            self._update_pixel_sensor()
            return self._default_image

    def _set_size(self, width=None, height=None):
        """Set output image size"""
        if width:
            self._image_width = width

        if self._preserve_aspect_ratio and width:
            self._image_height = int(width * (self._rows / self._cols))
        else:
            if height:
                self._image_height = height

    def _update_pixel_sensor(self):
        """Decode pixels from sensor and update camera image"""

        encoded_pixels = self.hass.states.get(self._pixel_sensor).state
        _LOGGER.debug("Decoding pixels: %s", encoded_pixels)
        if encoded_pixels not in [STATE_UNKNOWN, STATE_UNAVAILABLE]:
            data = []
            for char in base64.b64decode(encoded_pixels):
                if char & (1 << 11):
                    char &= ~(1 << 11)
                    char = char * -1
                data.append(char * 0.25)
            self._setup_range(data)
            self._default_image = self._camera_image(data)

    def _setup_range(self, pixels):
        """Perform auto-ranging"""
        self._pixel_min_temp = float(min(pixels))
        self._pixel_max_temp = float(max(pixels))
        if self._auto_range:
            _LOGGER.debug("Minimum temperature %s", self._pixel_min_temp)
            _LOGGER.debug("Maximum temperature %s", self._pixel_max_temp)
            if (
                self._pixel_min_temp != self._pixel_max_temp
                and self._pixel_max_temp > self._pixel_min_temp
                and not (
                    self._pixel_min_temp == self._min_temperature
                    and self._pixel_max_temp == self._max_temperature
                )
            ):
                self._min_temperature = self._pixel_min_temp
                self._max_temperature = self._pixel_max_temp
                diff = self._max_temperature - self._min_temperature

                if diff < self._min_diff:
                    self._max_temperature = self._min_temperature + self._min_diff

    def _setup_default_image(self):
        """Set up a default image"""
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

        if self._method != "disabled":
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
        else:
            image = Image.new("RGB", (self._image_width, self._image_height))
            draw = ImageDraw.Draw(image)
            pixel_width = self._image_width / self._cols
            pixel_height = self._image_height / self._rows
            for y, row in enumerate(pixels):
                for x, pixel in enumerate(row):
                    color_index = constrain(int(pixel), 0, self._color_depth - 1)
                    x0 = pixel_width * x
                    y0 = pixel_height * y
                    x1 = x0 + pixel_width
                    y1 = y0 + pixel_height
                    draw.rectangle(((x0, y0), (x1, y1)), fill=self._colors[color_index])

        # Add overlay
        if self._overlay:
            min_temp = (
                self._pixel_min_temp
                if self._temperature_unit == UnitOfTemperature.CELSIUS
                else TemperatureConverter.convert(
                    self._pixel_min_temp, UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT
                )
            )
            max_temp = (
                self._pixel_max_temp
                if self._temperature_unit == UnitOfTemperature.CELSIUS
                else TemperatureConverter.convert(
                    self._pixel_max_temp, UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT
                )
            )
            min_temperature = (
                self._min_temperature
                if self._temperature_unit == UnitOfTemperature.CELSIUS
                else TemperatureConverter.convert(
                    self._min_temperature, UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT
                )
            )
            max_temperature = (
                self._max_temperature
                if self._temperature_unit == UnitOfTemperature.CELSIUS
                else TemperatureConverter.convert(
                    self._max_temperature, UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT
                )
            )

            draw.multiline_text(
                (10, 10),
                f"Min: {min_temp}{self._temperature_unit}\nMax: {max_temp}{self._temperature_unit}\nRange: {min_temperature}{self._temperature_unit} - {max_temperature}{self._temperature_unit}",
                fill=(255, 255, 0),
            )

        # Return image
        with io.BytesIO() as output:
            if self._format == "jpeg":
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
