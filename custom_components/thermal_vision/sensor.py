"""Thermal Vision Sensor"""

import logging

import numpy as np

from datetime import timedelta

import voluptuous as vol

from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity

from homeassistant import util
from homeassistant.util import Throttle

from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    DEVICE_CLASS_TEMPERATURE,
    CONF_VERIFY_SSL,
    TEMP_FAHRENHEIT,
)

from .const import (
    ATTR_AVG,
    ATTR_MAX,
    ATTR_MAX_INDEX,
    ATTR_MIN,
    ATTR_MIN_INDEX,
    ATTR_SENSOR_TEMP,
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
    DEFAULT_VERIFY_SSL,
)

from .client import ThermalVisionClient

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend(
        {
            vol.Required(CONF_HOST): cv.url,
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
            vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): cv.boolean,
            vol.Optional(CONF_SCAN_INTERVAL): cv.time_period,
            vol.Optional(CONF_STATE, default=DEFAULT_STATE): vol.All(
                cv.string,
                vol.In(
                    (
                        ATTR_MIN,
                        ATTR_MAX,
                        ATTR_AVG,
                    )
                ),
            ),
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
    _LOGGER.debug("async setup Thermal Vision Sensor")
    async_add_entities([ThermalVisionSensor(hass, config)])


class ThermalVisionSensor(Entity):
    """Thermal Vision Sensor"""

    def __init__(self, hass, config) -> None:
        """Initialize Thermal Vision Sensor"""
        self._hass = hass
        self._name = config.get(CONF_NAME)
        _LOGGER.debug(f"Initialize Thermal Vision Sensor {self._name}")

        self._verify_ssl = config.get(CONF_VERIFY_SSL)
        self._client = ThermalVisionClient(config.get(CONF_HOST), self._verify_ssl)

        self._temperature_unit = hass.config.units.temperature_unit

        self._state = None
        self._icon = "mdi:grid"

        self._average_temp = None
        self._min_temp = None
        self._max_temp = None
        self._min_index = None
        self._max_index = None
        self._sensor_temp = None

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

        return self._temperature_unit

    @property
    def device_class(self):
        """Return the unit of measurement."""
        return DEVICE_CLASS_TEMPERATURE

    @property
    def device_state_attributes(self):
        """Return the attributes of the sensor."""
        return {
            ATTR_AVG: self._average_temp,
            ATTR_MIN: self._min_temp,
            ATTR_MAX: self._max_temp,
            ATTR_MIN_INDEX: self._min_index,
            ATTR_MAX_INDEX: self._max_index,
            ATTR_SENSOR_TEMP: self._sensor_temp,
        }

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._icon

    def _set_state(self):
        """Set state based on sensor type"""
        if self._state_type == ATTR_MAX:
            self._state = self._max_temp
        elif self._state_type == ATTR_MIN:
            self._state = self._min_temp
        elif self._state_type == ATTR_AVG:
            self._state = self._average_temp

        if self._state is None:
            self._available = False
        else:
            self._available = True

    def _update(self) -> None:
        try:
            self._client.call()
            pixels = self._client.get_raw()
            self._sensor_temp = self._client.get_temp()
            pixels = np.reshape(pixels, (self._rows, self._cols))

            pixels = pixels[
                self._roi[CONF_TOP] : self._roi[CONF_BOTTOM] + 1,
                self._roi[CONF_LEFT] : self._roi[CONF_RIGHT] + 1,
            ]

            self._average_temp = np.average(pixels)
            self._min_temp = np.amin(pixels)
            self._max_temp = np.amax(pixels)

            self._min_index = np.argmin(pixels).item()
            self._max_index = np.argmax(pixels).item()

            if self._temperature_unit == TEMP_FAHRENHEIT:
                self._average_temp = util.temperature.celsius_to_fahrenheit(
                    self._average_temp
                )
                self._min_temp = util.temperature.celsius_to_fahrenheit(self._min_temp)
                self._max_temp = util.temperature.celsius_to_fahrenheit(self._max_temp)
                if not self._sensor_temp is None:
                    self._sensor_temp = util.temperature.celsius_to_fahrenheit(
                        self._sensor_temp
                    )

            self._set_state()

        except Exception as err:
            _LOGGER.warning("Updating the sensor failed: %s", err)
            self._state = None
