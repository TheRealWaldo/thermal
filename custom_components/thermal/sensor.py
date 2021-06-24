"""Thermal grid sensor"""

import logging

import numpy as np

from datetime import timedelta

import voluptuous as vol

from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from homeassistant.util import Throttle

from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
)

from .const import (
    CONF_STATE,
    CONF_ROI,
    CONF_LEFT,
    CONF_TOP,
    CONF_RIGHT,
    CONF_BOTTOM,
    CONF_SENSOR,
    CONF_ROWS,
    CONF_COLS,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_STATE,
    DEFAULT_ROWS,
    DEFAULT_COLS,
)

from .client import Client

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend(
        {
            vol.Required(CONF_HOST): cv.url,
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
            vol.Optional(CONF_SCAN_INTERVAL): cv.time_period,
            vol.Optional(CONF_STATE, default=DEFAULT_STATE): cv.string,
            vol.Optional(CONF_ROI): vol.Schema(
                {
                    vol.Required(CONF_LEFT): cv.positive_int,
                    vol.Required(CONF_TOP): cv.positive_int,
                    vol.Required(CONF_RIGHT): cv.positive_int,
                    vol.Required(CONF_BOTTOM): cv.positive_int,
                }
            ),
            vol.Optional(CONF_SENSOR): vol.Schema(
                {
                    vol.Required(CONF_ROWS, default=DEFAULT_ROWS): cv.positive_int,
                    vol.Required(CONF_COLS, default=DEFAULT_COLS): cv.positive_int,
                }
            ),
        }
    )
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""
    async_add_entities([ThermalSensor(hass, config)])


class ThermalSensor(Entity):
    """Thermal sensor"""

    def __init__(self, hass, config) -> None:
        """Initialize thermal sensor"""
        self._hass = hass
        self._name = config.get(CONF_NAME)
        _LOGGER.debug(f"Initialize Thermal sensor {self._name}")

        self._client = Client(config.get(CONF_HOST))

        self._state = None
        self._icon = "mdi:grid"
        self._attributes = {}

        self._state_type = config.get(CONF_STATE)

        sensor = config.get(CONF_SENSOR)
        if sensor:
            self._rows = sensor.get(CONF_ROWS, DEFAULT_ROWS)
            self._cols = sensor.get(CONF_COLS, DEFAULT_COLS)
        else:
            self._rows = DEFAULT_ROWS
            self._cols = DEFAULT_COLS

        roi = config.get(CONF_ROI)
        if roi:
            self._roi = {
                "left": roi[CONF_LEFT],
                "top": roi[CONF_TOP],
                "right": roi[CONF_RIGHT],
                "bottom": roi[CONF_BOTTOM],
            }
        else:
            self._roi = {
                "left": 0,
                "top": 0,
                "right": self._cols - 1,
                "bottom": self._rows - 1,
            }

        interval = config.get(
            CONF_SCAN_INTERVAL, timedelta(seconds=DEFAULT_SCAN_INTERVAL)
        )
        self.update = Throttle(interval)(self._update)

    @property
    def should_poll(self):
        return True

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def device_class(self):
        """Return the unit of measurement."""
        return DEVICE_CLASS_TEMPERATURE

    @property
    def device_state_attributes(self):
        """Return the attributes of the sensor."""
        return self._attributes

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._icon

    def _update(self) -> None:
        try:
            # Get 1d array of sensor pixels
            pixels = self._client.get_raw()
            # Convert to 2D
            pixels = np.reshape(pixels, (self._rows, self._cols))
            # Extracy ROI
            pixels = pixels[
                self._roi["top"] : self._roi["bottom"] + 1,
                self._roi["left"] : self._roi["right"] + 1,
            ]
            # Temperature statistics
            average_temp = np.average(pixels)
            min_temp = np.amin(pixels)
            max_temp = np.amax(pixels)
            # Indexs
            min_index = np.argmin(pixels).item()
            max_index = np.argmax(pixels).item()
            # Calculate statistics
            self._attributes = {
                "average": average_temp,
                "min": min_temp,
                "max": max_temp,
                "min_index": min_index,
                "max_index": max_index,
            }
            if self._state_type == "max":
                self._state = max_temp
            elif self._state_type == "min":
                self._state = min_temp
            else:
                self._state = average_temp
        except Exception as e:
            self._state = None
