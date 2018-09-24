# -*- coding: utf-8 -*-
"""PREMIS reader and writer."""

from __future__ import absolute_import
import logging

from .premis import (
    PREMISElement,
    PREMISObject,
    PREMISEvent,
    PREMISAgent,
    data_to_premis,
    premis_to_data,
    data_find,
    data_find_all,
    data_find_text,
    data_find_text_or_all
)
from .utils import (
    XSI_NAMESPACE,
    PREMIS_2_2_VERSION,
    PREMIS_2_2_NAMESPACE,
    PREMIS_2_2_XSD,
    PREMIS_2_2_SCHEMA_LOCATION,
    PREMIS_2_2_NAMESPACES,
    PREMIS_2_2_META,
    PREMIS_3_0_VERSION,
    PREMIS_3_0_NAMESPACE,
    PREMIS_3_0_XSD,
    PREMIS_3_0_SCHEMA_LOCATION,
    PREMIS_3_0_NAMESPACES,
    PREMIS_3_0_META,
    PREMIS_VERSIONS_MAP,
    PREMIS_VERSION,
    NAMESPACES,
    PREMIS_META,
    PREMIS_SCHEMA_LOCATION,
    lxmlns,
    snake_to_camel_cap,
    snake_to_camel,
    camel_to_snake
)


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

__all__ = ['PREMISElement', 'PREMISObject', 'PREMISEvent', 'PREMISAgent',
           'data_to_premis', 'premis_to_data', 'data_find', 'data_find_all',
           'data_find_text', 'data_find_text_or_all', 'XSI_NAMESPACE',
           'PREMIS_2_2_VERSION', 'PREMIS_2_2_NAMESPACE', 'PREMIS_2_2_XSD',
           'PREMIS_2_2_SCHEMA_LOCATION', 'PREMIS_2_2_NAMESPACES',
           'PREMIS_2_2_META', 'PREMIS_3_0_VERSION', 'PREMIS_3_0_NAMESPACE',
           'PREMIS_3_0_XSD', 'PREMIS_3_0_SCHEMA_LOCATION',
           'PREMIS_3_0_NAMESPACES', 'PREMIS_3_0_META', 'PREMIS_VERSIONS_MAP',
           'PREMIS_VERSION', 'NAMESPACES', 'PREMIS_META',
           'PREMIS_SCHEMA_LOCATION', 'lxmlns', 'snake_to_camel_cap',
           'snake_to_camel', 'camel_to_snake']
