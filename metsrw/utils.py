# -*- coding: utf-8 -*-
from six.moves.urllib.parse import quote_plus, unquote_plus, urlparse, urlunparse


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
    "dc": "http://purl.org/dc/elements/1.1/",
}

SCHEMA_LOCATIONS = (
    "http://www.loc.gov/METS/ "
    + "http://www.loc.gov/standards/mets/version111/mets.xsd"
)


def lxmlns(arg):
    """ Return XPath-usable namespace. """
    return "{" + NAMESPACES[arg] + "}"


####################
# METSRW CONSTANTS #
####################

FILE_ID_PREFIX = "file-"
GROUP_ID_PREFIX = "Group-"


#################################
# HELPERS FOR MANIPULATING URLS #
#################################

URL_ENCODABLE_PARTS = ("path", "params", "query", "fragment")


def _urlendecode(url, func):
    """Encode or decode ``url`` by applying ``func`` to all of its
    URL-encodable parts.
    """
    parsed = urlparse(url)
    for attr in URL_ENCODABLE_PARTS:
        parsed = parsed._replace(**{attr: func(getattr(parsed, attr))})
    return urlunparse(parsed)


def urlencode(url):
    """Replace unsafe ASCII characters using percent encoding as per RFC3986:
    https://tools.ietf.org/html/rfc3986#section-2.1.
    """
    return _urlendecode(url, lambda val: quote_plus(val, safe="/"))


def urldecode(url):
    """Decode percent encoding introduced per RFC3986
    https://tools.ietf.org/html/rfc3986#section-2.1.
    """
    return _urlendecode(url, unquote_plus)
