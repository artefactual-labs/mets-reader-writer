from __future__ import absolute_import
import logging

from .exceptions import MetsError, ParseError
from .fsentry import FSEntry
from .metadata import AMDSec, SubSection, MDRef, MDWrap
from .mets import METSDocument
from .utils import (
    NAMESPACES,
    SCHEMA_LOCATIONS,
    lxmlns,
    FILE_ID_PREFIX,
    GROUP_ID_PREFIX
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
    report_string
)

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

__all__ = ['MetsError', 'ParseError', 'FSEntry', 'AMDSec', 'SubSection',
           'MDRef', 'MDWrap', 'METSDocument', 'NAMESPACES', 'SCHEMA_LOCATIONS',
           'lxmlns', 'FILE_ID_PREFIX', 'GROUP_ID_PREFIX', 'METS_XSD_PATH',
           'AM_SCT_PATH', 'AM_PNTR_SCT_PATH', 'get_schematron', 'validate',
           'get_xmlschema', 'xsd_validate', 'schematron_validate',
           'sct_report_string', 'xsd_error_log_string', 'report_string']
