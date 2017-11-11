from __future__ import absolute_import

from collections import OrderedDict
import logging
from lxml import etree

from .exceptions import ParseError
from .utils import lxmlns, NAMESPACES, DUBLINCORE_SCHEMA_LOCATIONS

LOGGER = logging.getLogger(__name__)


class DublinCoreXmlData(object):
    """
    An object representing a METS xmlData element containing a Dublin Core element.

    :raises ParseError: If the root element tag is not xmlData.
    """
    DC_ELEMENTS = ['title', 'creator', 'subject', 'description', 'publisher', 'contributor', 'date', 'format', 'identifier', 'source', 'relation', 'language', 'coverage', 'rights']

    def __init__(self, title=None, creator=None, subject=None, description=None, publisher=None, contributor=None, date=None, format=None, identifier=None, source=None, relation=None, language=None, coverage=None, rights=None):
        for element in self.DC_ELEMENTS:
            setattr(self, element, locals()[element])

    @classmethod
    def parse(cls, root):
        """
        Parse an xmlData element containing a Dublin Core dublincore element.

        :param root: Element or ElementTree to be parsed into an object.
        :raises ParseError: If the root is not xmlData or doesn't contain a dublincore element.
        """
        if root.tag != lxmlns('mets') + 'xmlData':
            raise ParseError('DublinCoreXmlData can only parse xmlData elements with mets namespace.')

        dc_el = root.find('dcterms:dublincore', namespaces=NAMESPACES)

        if dc_el is None or dc_el.tag != lxmlns('dcterms') + 'dublincore':
            raise ParseError('xmlData can only contain a dublincore element with the dcterms namespace.')

        args = []

        for element in DublinCoreXmlData.DC_ELEMENTS:
            args.append(dc_el.findtext("dc:" + element, namespaces=NAMESPACES))

        return cls(*args)

    fromtree = parse

    def serialize(self):
        nsmap = OrderedDict([
            ('mets', NAMESPACES['mets']),
            ('xsi', NAMESPACES['xsi']),
            ('xlink', NAMESPACES['xlink'])
        ])
        root = etree.Element(lxmlns('mets') + 'xmlData', nsmap=nsmap)
        root.append(self._serialize_dublincore())
        return root

    def _serialize_dublincore(self):
        nsmap = OrderedDict([
            ('dcterms', NAMESPACES['dcterms']),
            ('dc', NAMESPACES['dc'])
        ])
        attrib = {'{}schemaLocation'.format(lxmlns('xsi')): DUBLINCORE_SCHEMA_LOCATIONS}
        dc_root = etree.Element(lxmlns('dcterms') + 'dublincore', nsmap=nsmap, attrib=attrib)

        for element in DublinCoreXmlData.DC_ELEMENTS:
            dc_el = etree.Element(lxmlns('dc') + element)
            dc_el.text = getattr(self, element)
            dc_root.append(dc_el)

        return dc_root
