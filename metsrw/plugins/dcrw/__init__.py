from __future__ import absolute_import

import logging

from .dc import DublinCoreXmlData
from .utils import (
    NAMESPACES,
    DUBLINCORE_SCHEMA_LOCATIONS,
    lxmlns,
)
from .exceptions import (
    DcError,
    ConstructError,
    ParseError
)


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


__all__ = [
    'DublinCoreXmlData',
    'NAMESPACES',
    'DUBLINCORE_SCHEMA_LOCATIONS',
    'lxmlns',
    'DcError',
    'ConstructError',
    'ParseError',
]
