"""Thermal integration"""

import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant.const import (
    ATTR_ENTITY_ID,
)

from .const import DOMAIN, SERVICE_AUTO_SCALE

AUTO_SCALE_SERVICE_SCHEMA = vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_ids})

_LOGGER = logging.getLogger(__name__)


def setup(hass, config):
    """Setup platfrom"""

    async def async_auto_scale(call):
        """Call auto scale service handler."""
        await async_handle_auto_scale_service(hass, call)

    hass.services.register(
        DOMAIN,
        SERVICE_AUTO_SCALE,
        async_auto_scale,
        schema=AUTO_SCALE_SERVICE_SCHEMA,
    )

    return True


async def async_handle_auto_scale_service(hass, call):
    """Handle auto scale service calls."""
    entity_id = call.data[ATTR_ENTITY_ID]
    _LOGGER.debug(f"Auto scale {entity_id}")
