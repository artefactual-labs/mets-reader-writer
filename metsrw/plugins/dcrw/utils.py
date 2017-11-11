NAMESPACES = {
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "mets": "http://www.loc.gov/METS/",
    "premis": "info:lc/xmlns/premis-v2",
    "dcterms": "http://purl.org/dc/terms/",
    "fits": "http://hul.harvard.edu/ois/xml/ns/fits/fits_output",
    "xlink": "http://www.w3.org/1999/xlink",
    "dc": "http://purl.org/dc/elements/1.1/"
}

DUBLINCORE_SCHEMA_LOCATIONS = "http://purl.org/dc/terms/ " + \
                              "http://dublincore.org/schemas/xmls/qdc/2008/02/11/dcterms.xsd"


def lxmlns(arg):
    """ Return XPath-usable namespace. """
    return '{' + NAMESPACES[arg] + '}'
