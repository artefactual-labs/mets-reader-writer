"""METS reader and writer."""

import logging

from . import plugins
from .di import Dependency
from .di import FeatureBroker
from .di import feature_broker
from .di import has_class_methods
from .di import has_methods
from .di import is_class
from .di import set_feature_broker_to_default_state
from .exceptions import MetsError
from .exceptions import ParseError
from .fsentry import FSEntry
from .metadata import Agent
from .metadata import AltRecordID
from .metadata import AMDSec
from .metadata import MDRef
from .metadata import MDWrap
from .metadata import SubSection
from .mets import METSDocument
from .utils import FILE_ID_PREFIX
from .utils import GROUP_ID_PREFIX
from .utils import NAMESPACES
from .utils import SCHEMA_LOCATIONS
from .utils import generate_mdtype_key
from .utils import lxmlns
from .utils import urldecode
from .utils import urlencode
from .validate import AM_PNTR_SCT_PATH
from .validate import AM_SCT_PATH
from .validate import METS_XSD_PATH
from .validate import get_schematron
from .validate import get_xmlschema
from .validate import report_string
from .validate import schematron_validate
from .validate import sct_report_string
from .validate import validate
from .validate import xsd_error_log_string
from .validate import xsd_validate

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())
__version__ = "0.6.1"

__all__ = [
    "Agent",
    "AltRecordID",
    "AMDSec",
    "AM_PNTR_SCT_PATH",
    "AM_SCT_PATH",
    "Dependency",
    "FILE_ID_PREFIX",
    "FSEntry",
    "FeatureBroker",
    "GROUP_ID_PREFIX",
    "MDRef",
    "MDWrap",
    "METSDocument",
    "METS_XSD_PATH",
    "MetsError",
    "NAMESPACES",
    "ParseError",
    "SCHEMA_LOCATIONS",
    "SubSection",
    "__version__",
    "feature_broker",
    "generate_mdtype_key",
    "get_schematron",
    "get_xmlschema",
    "has_class_methods",
    "has_methods",
    "is_class",
    "lxmlns",
    "plugins",
    "report_string",
    "schematron_validate",
    "sct_report_string",
    "set_feature_broker_to_default_state",
    "urldecode",
    "urlencode",
    "validate",
    "xsd_error_log_string",
    "xsd_validate",
]
