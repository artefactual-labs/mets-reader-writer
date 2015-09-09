# LXML HELPERS

NAMESPACES = {
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "mets": "http://www.loc.gov/METS/",
    "premis": "info:lc/xmlns/premis-v2",
    "dcterms": "http://purl.org/dc/terms/",
    "fits": "http://hul.harvard.edu/ois/xml/ns/fits/fits_output",
    "xlink": "http://www.w3.org/1999/xlink",
    "dc": "http://purl.org/dc/elements/1.1/"
}

SCHEMA_LOCATIONS = "http://www.loc.gov/METS/ " + \
                   "http://www.loc.gov/standards/mets/version18/mets.xsd"


def lxmlns(arg):
    """ Return XPath-usable namespace. """
    return '{' + NAMESPACES[arg] + '}'


# CONSTANTS

FILE_ID_PREFIX = 'file-'
GROUP_ID_PREFIX = 'Group-'
