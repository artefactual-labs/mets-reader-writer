from __future__ import absolute_import

import logging

from .object import (
    Object,
    ObjectCharacteristics
)
from .event import Event
from .utils import (
    NAMESPACES,
    PREMIS_SCHEMA_LOCATIONS,
    PREMIS_VERSION,
    lxmlns,
    append_text_as_element_if_not_none
)
from .exceptions import (
    PremisError,
    ConstructError,
    ParseError
)


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


__all__ = [
    'Object',
    'ObjectCharacteristics',
    'Event',
    'NAMESPACES',
    'PREMIS_SCHEMA_LOCATIONS',
    'PREMIS_VERSION',
    'lxmlns',
    'append_text_as_element_if_not_none',
    'PremisError',
    'ConstructError',
    'ParseError'
]
