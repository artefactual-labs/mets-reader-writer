from lxml import etree

NAMESPACES = {
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "premis": "info:lc/xmlns/premis-v2",
    "fits": "http://hul.harvard.edu/ois/xml/ns/fits/fits_output",
    "xlink": "http://www.w3.org/1999/xlink",
}

PREMIS_SCHEMA_LOCATIONS = "info:lc/xmlns/premis-v2 " + \
                          "http://www.loc.gov/standards/premis/v2/premis-v2-2.xsd"

PREMIS_VERSION = "2.2"


def lxmlns(arg):
    """ Return XPath-usable namespace. """
    return '{' + NAMESPACES[arg] + '}'


def append_text_as_element_if_not_none(parent_el, text, namespace, element_name):
    """ If a string is supplied, create a node with it and append it to a parent element """
    if text is not None:
        el = etree.Element(lxmlns(namespace) + element_name)
        el.text = text
        parent_el.append(el)
