"""PREMIS reader and writer."""

import logging

from .premis import PREMISAgent
from .premis import PREMISElement
from .premis import PREMISEvent
from .premis import PREMISObject
from .premis import PREMISRights
from .premis import data_find
from .premis import data_find_all
from .premis import data_find_text
from .premis import data_find_text_or_all
from .premis import data_to_premis
from .premis import premis_to_data
from .utils import NAMESPACES
from .utils import PREMIS_2_1_META
from .utils import PREMIS_2_1_NAMESPACE
from .utils import PREMIS_2_1_NAMESPACES
from .utils import PREMIS_2_1_SCHEMA_LOCATION
from .utils import PREMIS_2_1_VERSION
from .utils import PREMIS_2_1_XSD
from .utils import PREMIS_2_2_META
from .utils import PREMIS_2_2_NAMESPACE
from .utils import PREMIS_2_2_NAMESPACES
from .utils import PREMIS_2_2_SCHEMA_LOCATION
from .utils import PREMIS_2_2_VERSION
from .utils import PREMIS_2_2_XSD
from .utils import PREMIS_3_0_META
from .utils import PREMIS_3_0_NAMESPACE
from .utils import PREMIS_3_0_NAMESPACES
from .utils import PREMIS_3_0_SCHEMA_LOCATION
from .utils import PREMIS_3_0_VERSION
from .utils import PREMIS_3_0_XSD
from .utils import PREMIS_META
from .utils import PREMIS_SCHEMA_LOCATION
from .utils import PREMIS_VERSION
from .utils import PREMIS_VERSIONS_MAP
from .utils import XSI_NAMESPACE
from .utils import camel_to_snake
from .utils import lxmlns
from .utils import snake_to_camel
from .utils import snake_to_camel_cap

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

__all__ = [
    "PREMISElement",
    "PREMISObject",
    "PREMISEvent",
    "PREMISAgent",
    "PREMISRights",
    "data_to_premis",
    "premis_to_data",
    "data_find",
    "data_find_all",
    "data_find_text",
    "data_find_text_or_all",
    "XSI_NAMESPACE",
    "PREMIS_2_1_VERSION",
    "PREMIS_2_1_NAMESPACE",
    "PREMIS_2_1_XSD",
    "PREMIS_2_1_SCHEMA_LOCATION",
    "PREMIS_2_1_NAMESPACES",
    "PREMIS_2_1_META",
    "PREMIS_2_2_VERSION",
    "PREMIS_2_2_NAMESPACE",
    "PREMIS_2_2_XSD",
    "PREMIS_2_2_SCHEMA_LOCATION",
    "PREMIS_2_2_NAMESPACES",
    "PREMIS_2_2_META",
    "PREMIS_3_0_VERSION",
    "PREMIS_3_0_NAMESPACE",
    "PREMIS_3_0_XSD",
    "PREMIS_3_0_SCHEMA_LOCATION",
    "PREMIS_3_0_NAMESPACES",
    "PREMIS_3_0_META",
    "PREMIS_VERSIONS_MAP",
    "PREMIS_VERSION",
    "NAMESPACES",
    "PREMIS_META",
    "PREMIS_SCHEMA_LOCATION",
    "lxmlns",
    "snake_to_camel_cap",
    "snake_to_camel",
    "camel_to_snake",
]
