"""Thermal Vision Binary Sensor"""

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
    CONF_VERIFY_SSL,
)

from .const import (
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
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
        }
    )
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""
    _LOGGER.debug("async setup Thermal Vision Sensor")
    async_add_entities([ThermalVisionBinarySensor(hass, config)])


class ThermalVisionBinarySensor(Entity):
    """Thermal Vision Binary Sensor"""

    def __init__(self, hass, config) -> None:
        """Initialize Thermal Vision Binary Sensor"""
        self._hass = hass
        self._name = config.get(CONF_NAME)
        _LOGGER.debug(f"Initialize Thermal Vision Binary Sensor {self._name}")

        self._verify_ssl = config.get(CONF_VERIFY_SSL)
        self._client = ThermalVisionClient(config.get(CONF_HOST), self._verify_ssl)
        self._person_detected = None

        self._state = None
        self._icon = "mdi:grid"

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
    def device_class(self):
        """Return the device class."""
        return "occupancy"

    def _set_state(self):
        """Set state based on sensor type"""
        if self._person_detected:
            self._state = "on"
        else:
            if self._person_detected is None:
                self._state = None
            else:
                self._state = "off"

        if self._state is None:
            self._available = False
        else:
            self._available = True

    def _update(self) -> None:
        try:
            self._client.call()
            self._person_detected = self._client.get_person_detected()

            if self._person_detected:
                _LOGGER.debug(f"{self._name} shows a person detected")

            self._set_state()

        except Exception as err:
            _LOGGER.warning("Updating the sensor failed: %s", err)
            self._state = None
