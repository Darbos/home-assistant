"""
Component for interacting with a Lutron RadioRA 2 system.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/lutron/
"""
import logging

from homeassistant.helpers import discovery
from homeassistant.helpers.entity import (Entity, generate_entity_id)
from homeassistant.loader import get_component

REQUIREMENTS = ['https://github.com/scottjgibson/pylutron'
                '/archive/master.zip'
                '#pylutron==0.2']
DOMAIN = 'lutron'

_LOGGER = logging.getLogger(__name__)

LUTRON_CONTROLLER = 'lutron_controller'
LUTRON_DEVICES = 'lutron_devices'
LUTRON_GROUPS = 'lutron_groups'


def setup(hass, base_config):
    """Setup the Lutron component."""
    from pylutron import Lutron

    hass.data[LUTRON_CONTROLLER] = None
    hass.data[LUTRON_DEVICES] = {'light':[], 'binary_sensor': []}
    hass.data[LUTRON_GROUPS] = {}

    config = base_config.get(DOMAIN)
    hass.data[LUTRON_CONTROLLER] = Lutron(
        config['host'],
        config['user'],
        config['password'],
        config['caseta']
    )

    if(config['caseta']):
        hass.data[LUTRON_CONTROLLER].load_json_db(config['caseta_config'])
    else:
        hass.data[LUTRON_CONTROLLER].load_xml_db()

    hass.data[LUTRON_CONTROLLER].connect()
    _LOGGER.info("Connected to Main Repeater at %s", config['host'])

    group = get_component('group')
    # Sort our devices into types
    for area in hass.data[LUTRON_CONTROLLER].areas:
        if area.name not in hass.data[LUTRON_GROUPS]:
            grp = group.Group.create_group(hass, area.name, [])
            hass.data[LUTRON_GROUPS][area.name] = grp
        for output in area.outputs:
            hass.data[LUTRON_DEVICES]['light'].append((area.name, output))
        for keypad in area.keypads:
            for button in keypad.buttons:
                hass.data[LUTRON_DEVICES]['binary_sensor'].append((area.name, button))
    for component in ('light', 'binary_sensor',):
        discovery.load_platform(hass, component, DOMAIN, None, base_config)
    return True


class LutronDevice(Entity):
    """Representation of a Lutron device entity."""

    def __init__(self, hass, domain, area_name, lutron_device, controller):
        """Initialize the device."""
        self._lutron_device = lutron_device
        self._controller = controller
        self._area_name = area_name

        self.hass = hass
        object_id = '{} {}'.format(area_name, lutron_device.name)
        self.entity_id = generate_entity_id(domain + '.{}', object_id,
                                            hass=hass)

        self._controller.subscribe(self._lutron_device, self._update_callback)

    def _update_callback(self, _device):
        """Callback invoked by pylutron when the device state changes."""
        self.schedule_update_ha_state()

    @property
    def name(self):
        """Return the name of the device."""
        return self._lutron_device.name

    @property
    def should_poll(self):
        """No polling needed."""
        return False
