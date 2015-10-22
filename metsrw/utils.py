from lxml import etree

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

METS_SCHEMA_LOCATIONS = "http://www.loc.gov/METS/ " + \
                        "http://www.loc.gov/standards/mets/version18/mets.xsd"

PREMIS_SCHEMA_LOCATIONS = "info:lc/xmlns/premis-v2 " + \
                          "http://www.loc.gov/standards/premis/v2/premis-v2-2.xsd"

PREMIS_VERSION = "2.2"


DUBLINCORE_SCHEMA_LOCATIONS = "http://purl.org/dc/terms/ " + \
                              "http://dublincore.org/schemas/xmls/qdc/2008/02/11/dcterms.xsd"


def lxmlns(arg):
    """ Return XPath-usable namespace. """
    return '{' + NAMESPACES[arg] + '}'


def append_text_as_element_if_not_none(parent_el, text, namespace, element_name):
    """ If a string is supplied, create a node with it and append it to a parent element """
    if text is not None:
        el = etree.Element(lxmlns(namespace) + element_name)
        el.text = text
        parent_el.append(el)


# CONSTANTS

FILE_ID_PREFIX = 'file-'
GROUP_ID_PREFIX = 'Group-'
