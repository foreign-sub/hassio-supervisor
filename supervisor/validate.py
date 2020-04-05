"""Validate functions."""
import ipaddress
import re
import uuid

import voluptuous as vol

from .const import ATTR_ACCESS_TOKEN
from .const import ATTR_ADDONS_CUSTOM_LIST
from .const import ATTR_AUDIO
from .const import ATTR_AUDIO_INPUT
from .const import ATTR_AUDIO_OUTPUT
from .const import ATTR_BOOT
from .const import ATTR_CHANNEL
from .const import ATTR_CLI
from .const import ATTR_DEBUG
from .const import ATTR_DEBUG_BLOCK
from .const import ATTR_DNS
from .const import ATTR_HASSOS
from .const import ATTR_HOMEASSISTANT
from .const import ATTR_IMAGE
from .const import ATTR_LAST_BOOT
from .const import ATTR_LOGGING
from .const import ATTR_MULTICAST
from .const import ATTR_PORT
from .const import ATTR_PORTS
from .const import ATTR_REFRESH_TOKEN
from .const import ATTR_SESSION
from .const import ATTR_SSL
from .const import ATTR_SUPERVISOR
from .const import ATTR_TIMEZONE
from .const import ATTR_UUID
from .const import ATTR_VERSION
from .const import ATTR_WAIT_BOOT
from .const import ATTR_WATCHDOG
from .const import UpdateChannels
from .utils.validate import validate_timezone

RE_REPOSITORY = re.compile(r"^(?P<url>[^#]+)(?:#(?P<branch>[\w\-]+))?$")

# pylint: disable=no-value-for-parameter
# pylint: disable=invalid-name
network_port = vol.All(vol.Coerce(int), vol.Range(min=1, max=65535))
wait_boot = vol.All(vol.Coerce(int), vol.Range(min=1, max=60))
docker_image = vol.Match(r"^[\w{}]+/[\-\w{}]+$")
uuid_match = vol.Match(r"^[0-9a-f]{32}$")
sha256 = vol.Match(r"^[0-9a-f]{64}$")
token = vol.Match(r"^[0-9a-f]{32,256}$")
log_level = vol.In(["debug", "info", "warning", "error", "critical"])


def dns_url(url: str) -> str:
    """ takes a DNS url (str) and validates that it matches the scheme dns://<ip address>."""
    if not url.lower().startswith("dns://"):
        raise vol.Invalid("Doesn't start with dns://")
    address: str = url[6:]  # strip the dns:// off
    try:
        ipaddress.ip_address(address)  # matches ipv4 or ipv6 addresses
    except ValueError:
        raise vol.Invalid("Invalid DNS URL: {}".format(url))
    return url


dns_server_list = vol.All(vol.Length(max=8), [dns_url])


def validate_repository(repository: str) -> str:
    """Validate a valid repository."""
    data = RE_REPOSITORY.match(repository)
    if not data:
        raise vol.Invalid("No valid repository format!")

    # Validate URL
    # pylint: disable=no-value-for-parameter
    vol.Url()(data.group("url"))

    return repository


# pylint: disable=no-value-for-parameter
repositories = vol.All([validate_repository], vol.Unique())


DOCKER_PORTS = vol.Schema(
    {
        vol.All(vol.Coerce(str), vol.Match(r"^\d+(?:/tcp|/udp)?$")): vol.Maybe(
            network_port
        )
    }
)

DOCKER_PORTS_DESCRIPTION = vol.Schema(
    {vol.All(vol.Coerce(str), vol.Match(r"^\d+(?:/tcp|/udp)?$")): vol.Coerce(str)}
)


# pylint: disable=no-value-for-parameter
SCHEMA_HASS_CONFIG = vol.Schema(
    {
        vol.Optional(ATTR_UUID, default=lambda: uuid.uuid4().hex): uuid_match,
        vol.Optional(ATTR_VERSION): vol.Maybe(vol.Coerce(str)),
        vol.Optional(ATTR_IMAGE): docker_image,
        vol.Optional(ATTR_ACCESS_TOKEN): token,
        vol.Optional(ATTR_BOOT, default=True): vol.Boolean(),
        vol.Optional(ATTR_PORT, default=8123): network_port,
        vol.Optional(ATTR_REFRESH_TOKEN): vol.Maybe(vol.Coerce(str)),
        vol.Optional(ATTR_SSL, default=False): vol.Boolean(),
        vol.Optional(ATTR_WATCHDOG, default=True): vol.Boolean(),
        vol.Optional(ATTR_WAIT_BOOT, default=600): vol.All(
            vol.Coerce(int), vol.Range(min=60)
        ),
        vol.Optional(ATTR_AUDIO_OUTPUT, default=None): vol.Maybe(vol.Coerce(str)),
        vol.Optional(ATTR_AUDIO_INPUT, default=None): vol.Maybe(vol.Coerce(str)),
    },
    extra=vol.REMOVE_EXTRA,
)


SCHEMA_UPDATER_CONFIG = vol.Schema(
    {
        vol.Optional(ATTR_CHANNEL, default=UpdateChannels.STABLE): vol.Coerce(
            UpdateChannels
        ),
        vol.Optional(ATTR_HOMEASSISTANT): vol.Coerce(str),
        vol.Optional(ATTR_SUPERVISOR): vol.Coerce(str),
        vol.Optional(ATTR_HASSOS): vol.Coerce(str),
        vol.Optional(ATTR_CLI): vol.Coerce(str),
        vol.Optional(ATTR_DNS): vol.Coerce(str),
        vol.Optional(ATTR_AUDIO): vol.Coerce(str),
        vol.Optional(ATTR_MULTICAST): vol.Coerce(str),
        vol.Optional(ATTR_IMAGE, default=dict): vol.Schema(
            {
                vol.Optional(ATTR_HOMEASSISTANT): docker_image,
                vol.Optional(ATTR_SUPERVISOR): docker_image,
                vol.Optional(ATTR_CLI): docker_image,
                vol.Optional(ATTR_DNS): docker_image,
                vol.Optional(ATTR_AUDIO): docker_image,
                vol.Optional(ATTR_MULTICAST): docker_image,
            },
            extra=vol.REMOVE_EXTRA,
        ),
    },
    extra=vol.REMOVE_EXTRA,
)


# pylint: disable=no-value-for-parameter
SCHEMA_SUPERVISOR_CONFIG = vol.Schema(
    {
        vol.Optional(ATTR_TIMEZONE, default="UTC"): validate_timezone,
        vol.Optional(ATTR_LAST_BOOT): vol.Coerce(str),
        vol.Optional(
            ATTR_ADDONS_CUSTOM_LIST,
            default=["https://github.com/hassio-addons/repository"],
        ): repositories,
        vol.Optional(ATTR_WAIT_BOOT, default=5): wait_boot,
        vol.Optional(ATTR_LOGGING, default="info"): log_level,
        vol.Optional(ATTR_DEBUG, default=False): vol.Boolean(),
        vol.Optional(ATTR_DEBUG_BLOCK, default=False): vol.Boolean(),
    },
    extra=vol.REMOVE_EXTRA,
)


SCHEMA_AUTH_CONFIG = vol.Schema({sha256: sha256})


SCHEMA_INGRESS_CONFIG = vol.Schema(
    {
        vol.Required(ATTR_SESSION, default=dict): vol.Schema(
            {token: vol.Coerce(float)}
        ),
        vol.Required(ATTR_PORTS, default=dict): vol.Schema(
            {vol.Coerce(str): network_port}
        ),
    },
    extra=vol.REMOVE_EXTRA,
)
