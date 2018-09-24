# -*- coding: utf-8 -*-
# Namespaces, etc.

XSI_NAMESPACE = 'http://www.w3.org/2001/XMLSchema-instance'

# PREMIS v. 2.2
PREMIS_2_2_VERSION = '2.2'
PREMIS_2_2_NAMESPACE = 'info:lc/xmlns/premis-v2'
PREMIS_2_2_XSD = 'http://www.loc.gov/standards/premis/v2/premis-v2-2.xsd'
PREMIS_2_2_SCHEMA_LOCATION = '{} {}'.format(
    PREMIS_2_2_NAMESPACE, PREMIS_2_2_XSD)
PREMIS_2_2_NAMESPACES = {
    'premis': PREMIS_2_2_NAMESPACE,
    'xsi': XSI_NAMESPACE
}
PREMIS_2_2_META = {
    'xsi:schema_location': PREMIS_2_2_SCHEMA_LOCATION,
    'version': PREMIS_2_2_VERSION
}

# PREMIS v. 3.0
PREMIS_3_0_VERSION = '3.0'
PREMIS_3_0_NAMESPACE = 'http://www.loc.gov/premis/v3'
PREMIS_3_0_XSD = 'http://www.loc.gov/standards/premis/v3/premis.xsd'
PREMIS_3_0_SCHEMA_LOCATION = '{} {}'.format(
    PREMIS_3_0_NAMESPACE, PREMIS_3_0_XSD)
PREMIS_3_0_NAMESPACES = {
    'premis': PREMIS_3_0_NAMESPACE,
    'xsi': XSI_NAMESPACE
}
PREMIS_3_0_META = {
    'xsi:schema_location': PREMIS_3_0_SCHEMA_LOCATION,
    'version': PREMIS_3_0_VERSION
}

PREMIS_VERSIONS_MAP = {
    PREMIS_2_2_VERSION: {
        'namespaces': PREMIS_2_2_NAMESPACES,
        'meta': PREMIS_2_2_META
    },
    PREMIS_3_0_VERSION: {
        'namespaces': PREMIS_3_0_NAMESPACES,
        'meta': PREMIS_3_0_META
    }
}

# Treat PREMIS v. 2.2 as the default (for now).
PREMIS_VERSION = PREMIS_2_2_VERSION
NAMESPACES = PREMIS_VERSIONS_MAP[PREMIS_VERSION]['namespaces']
PREMIS_META = PREMIS_VERSIONS_MAP[PREMIS_VERSION]['meta']
PREMIS_SCHEMA_LOCATION = PREMIS_2_2_SCHEMA_LOCATION


def lxmlns(arg, premis_version=PREMIS_VERSION):
    """Return XPath-usable namespace."""
    namespaces = PREMIS_VERSIONS_MAP[premis_version]['namespaces']
    return '{' + namespaces[arg] + '}'


def snake_to_camel_cap(snake):
    """Convert snake_case to CamelCaseCapitalized."""
    return ''.join([word.capitalize() for word in snake.split('_')])


def snake_to_camel(snake):
    """Convert snake_case to camelCase."""
    tmp = snake_to_camel_cap(snake)
    return tmp[0].lower() + tmp[1:]


def camel_to_snake(camel):
    """Convert camelCase to snake_case."""
    ret = []
    last_lower = False
    for char in camel:
        current_upper = char.upper() == char
        if current_upper and last_lower:
            ret.append('_')
            ret.append(char.lower())
        else:
            ret.append(char.lower())
        last_lower = not current_upper
    return ''.join(ret)
