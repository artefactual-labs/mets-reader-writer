# -*- coding: utf-8 -*-
from six.moves.urllib.parse import quote_plus, urlparse, urlunparse


####################################
# LXML HELPER VALUES AND FUNCTIONS #
####################################

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
                   "http://www.loc.gov/standards/mets/version111/mets.xsd"


def lxmlns(arg):
    """ Return XPath-usable namespace. """
    return '{' + NAMESPACES[arg] + '}'


####################
# METSRW CONSTANTS #
####################

FILE_ID_PREFIX = 'file-'
GROUP_ID_PREFIX = 'Group-'


#################################
# HELPERS FOR MANIPULATING URLS #
#################################

def urlencode(url):
    """Replace unsafe ASCII characters using percent encoding as per RFC3986:
    https://tools.ietf.org/html/rfc3986#section-2.1.
    """
    parsed = urlparse(url)
    for attr in ('path', 'params', 'query', 'fragment'):
        parsed = parsed._replace(
            **{attr: quote_plus(getattr(parsed, attr), safe='/')})
    return urlunparse(parsed)
