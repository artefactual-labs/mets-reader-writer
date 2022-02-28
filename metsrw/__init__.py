# -*- coding: utf-8 -*-
"""METS reader and writer."""

from __future__ import absolute_import
import logging

from .exceptions import MetsError, ParseError
from .fsentry import FSEntry
from .metadata import Agent, AltRecordID, AMDSec, SubSection, MDRef, MDWrap
from .mets import METSDocument
from .utils import (
    NAMESPACES,
    SCHEMA_LOCATIONS,
    lxmlns,
    FILE_ID_PREFIX,
    GROUP_ID_PREFIX,
    urlencode,
    urldecode,
    generate_mdtype_key,
)
from .validate import (
    METS_XSD_PATH,
    AM_SCT_PATH,
    AM_PNTR_SCT_PATH,
    get_schematron,
    validate,
    get_xmlschema,
    xsd_validate,
    schematron_validate,
    sct_report_string,
    xsd_error_log_string,
    report_string,
)
from .di import (
    FeatureBroker,
    set_feature_broker_to_default_state,
    feature_broker,
    Dependency,
    has_class_methods,
    has_methods,
    is_class,
)
from . import plugins

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())
__version__ = "0.3.21"

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
