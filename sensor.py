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
from homeassistant.helpers import device_registry as dr
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
    """Set up the device and sensors"""
    _LOGGER.info("Setting up the Environment UK Flood Sensor")
    # get the configuration
    fsensor = {
        "name" : config[CONF_NAME],
        "notation" : config[CONF_ID],
    }
    # create the device
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=f"ukenv_fs_{fsensor['notation']}",
        name=f"ukenv_fs_{fsensor['notation']}",
        manufacturer="UK Environmental Agency",
        model="Environment Agency Real Time flood-monitoring API",
        sw_version="0.9",
        identifiers={("envuk_flood_api", f"ukenv_fs_{fsensor["notation"]}")},
    )
    # add the sensors
    add_entities([
        FloodSensorDatum(fsensor),
        FloodSensorSeaLevel(fsensor),
    ])

# Base class for the sensors
class FloodSensor(SensorEntity):
    """Representation of a Flood Sensor"""

    # Sensor initialization
    def __init__(self, fsensor) -> None:
        """Initialize the sensor"""
        _LOGGER.info("Initialising the Environment UK Flood Sensor")
#        _LOGGER.info(str(fsensor.keys()))
        self._state = None
        self._attr_name = fsensor["name"]
        self._attr_id = fsensor["notation"]
        self._attr_native_unit_of_measurement = UnitOfLength.METERS
        self._attr_device_class = SensorDeviceClass.DISTANCE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        st_data = self.get_st_info()
        self._attr_latitude = st_data["latitude"]
        self._attr_longitude = st_data["longitude"]
        self._attr_datum = st_data["stageScale"]["datum"]

    # Device
    @property
    def device_class(self) -> str:
        """Return the device class of the sensor"""
        return self._attr_device_class

    @property
    def device_info(self) -> dr.DeviceInfo:
        """Return device information."""
        # Identifiers are what group entities into the same device.
        # If your device is created elsewhere, you can just specify the indentifiers parameter.
        # If your device connects via another device, add via_device parameter with the indentifiers of that device.
        return dr.DeviceInfo(
            name=f"ukenv_fs_{self._attr_id}",
            manufacturer="UK Environmental Agency",
            model="Environment Agency Real Time flood-monitoring API",
            sw_version="0.9",
            identifiers={("envuk_flood_api", f"ukenv_fs_{self._attr_id}")},
        )

    # Sensor properties
    @property
    def name(self) -> str:
        """Return the name of the sensor"""
        return self._attr_name

    @property
    def native_value(self) -> int | float:
        """Return the state of the entity."""
        # Using native value and native unit of measurement, allows you to change units
        # in Lovelace and HA will automatically calculate the correct value.
        return float(self._state)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement"""
        return self._attr_native_unit_of_measurement

    @property
    def state_class(self) -> str:
        """Return the state class of the sensor"""
        return self._attr_state_class

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this sensor."""
        return f"ukenv_fs_{self._attr_id}_mASD"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes"""
        return {
            "latitude": self._attr_latitude,
            "longitude": self._attr_longitude,
        }

    # Sensor helpers
    def get_st_info(self) -> dict:
        """Fetch the station information from the API"""
        _LOGGER.info("Fetching the station information")
        url = f"https://environment.data.gov.uk/flood-monitoring/id/stations/{self._attr_id}.json"
        _LOGGER.info(url)
        response = requests.get(url, timeout=10)
        data = response.json()
        st_data = {
            "latitude": data['items']['lat'],
            "longitude": data['items']['long'],
        }
        return st_data

# Sensor class for height from datum
class FloodSensorDatum(FloodSensor):
    """Water height above datum"""
    
    # Sensor update
    def update(self) -> None:
        """Update the sensor"""
        _LOGGER.info("Updating the Environment UK Flood Sensor - Datum")
        url = f"https://environment.data.gov.uk/flood-monitoring/id/stations/{self._attr_id}/readings?latest"
        _LOGGER.debug(url)
        response = requests.get(url, timeout=10)
        data = response.json()
        self._state = data['items'][0]['value']

# Sensor class for sea level
class FloodSensorSeaLevel(FloodSensor):
    """Water height above sea level"""
    
    # Sensor update
    def update(self) -> None:
        """Update the sensor"""
        _LOGGER.info("Updating the Environment UK Flood Sensor - Sea Level")
        url = f"https://environment.data.gov.uk/flood-monitoring/id/stations/{self._attr_id}/readings?latest"
        _LOGGER.debug(url)
        response = requests.get(url, timeout=10)
        data = response.json()
        self._state = data['items'][0]['value'] + self._attr_datum
