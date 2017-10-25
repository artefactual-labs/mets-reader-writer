# LXML HELPERS

NAMESPACES = {
    "premis": "info:lc/xmlns/premis-v2",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

PREMIS_VERSION = '2.2'
PREMIS_SCHEMA_LOCATION = (
    'info:lc/xmlns/premis-v2'
    ' http://www.loc.gov/standards/premis/v2/premis-v2-2.xsd')
PREMIS_META = {
    'xsi:schema_location': PREMIS_SCHEMA_LOCATION,
    'version': PREMIS_VERSION
}


def lxmlns(arg):
    """Return XPath-usable namespace."""
    return '{' + NAMESPACES[arg] + '}'


def snake_to_camel_cap(snake):
    """Convert snake_case to CamelCaseCapitalized."""
    return ''.join([word.capitalize() for word in snake.split('_')])


def snake_to_camel(snake):
    """Convert snake_case to camelCase."""
    tmp = snake_to_camel_cap(snake)
    return tmp[0].lower() + tmp[1:]


def camel_to_snake(camel):
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
