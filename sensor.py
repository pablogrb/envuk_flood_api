"""Environment UK Real Time Flood Monitoring API sensor integration"""
from __future__ import annotations

import logging
from datetime import timedelta

import requests
import voluptuous as vol

from homeassistant.components.sensor import (PLATFORM_SCHEMA,
                                             SensorDeviceClass, SensorEntity,
                                             SensorStateClass)
from homeassistant.const import CONF_ID, CONF_NAME, UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

# Configuration schema
DEFAULT_NAME = "Environment UK Flood Sensor"
SCAN_INTERVAL = timedelta(minutes=15)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME): str,
    vol.Required(CONF_ID): str,
})

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor"""
    _LOGGER.info("Setting up the Environment UK Flood Sensor")
    fsensor = {
        "name" : config[CONF_NAME],
        "notation" : config[CONF_ID],
    }
    add_entities([FloodSensor(fsensor)])

class FloodSensor(SensorEntity):
    """Representation of a Flood Sensor"""

    def __init__(self, fsensor) -> None:
        """Initialize the sensor"""
        _LOGGER.info("Initialising the Environment UK Flood Sensor")
        self._attr_name = fsensor["name"]
        self._state = None
        self._attr_native_unit_of_measurement = UnitOfLength.METERS
        self._attr_device_class = SensorDeviceClass.DISTANCE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self) -> str:
        """Return the name of the sensor"""
        return self._attr_name

    @property
    def state(self) -> float:
        """Return the state of the sensor"""
        return self._state

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement"""
        return self._attr_native_unit_of_measurement

    def update(self) -> None:
        """Update the sensor"""
        _LOGGER.info("Updating the Environment UK Flood Sensor")
        url = f"https://environment.data.gov.uk/flood-monitoring/id/stations/{self._attr_name}/readings?latest"
        response = requests.get(url, timeout=10)
        data = response.json()
        self._state = data["value"]
