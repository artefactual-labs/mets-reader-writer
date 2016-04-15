"""
Classes for metadata sections of the METS. Include amdSec, dmdSec, techMD, rightsMD, sourceMD, digiprovMD, mdRef and mdWrap.
"""
from __future__ import absolute_import

from collections import OrderedDict
import logging
from lxml import etree
from random import randint

import six

from . import exceptions
from . import utils

LOGGER = logging.getLogger(__name__)


class AMDSec(object):
    """
    An object representing a section of administrative metadata in a
    document.

    This is ordinarily created by :class:`metsrw.mets.METSDocument` instances and does not
    have to be instantiated directly.

    :param str section_id: ID of the section. If not provided, will be generated from 'amdSec' and a random number.
    :param list subsections: List of :class:`SubSection` that are part of this amdSec
    """
    tag = 'amdSec'

    def __init__(self, section_id=None, subsections=None):
        if subsections is None:
            subsections = []
        self.subsections = subsections
        self._id = section_id

    def id_string(self, force_generate=False):
        """
        Returns the ID string for the amdSec.

        :param bool force_generate: If True, will generate a new ID from 'amdSec' and a random number.
        """
        # e.g., amdSec_1
        if force_generate or not self._id:
            self._id = self.tag + '_' + str(randint(1, 999999))
        return self._id

    @classmethod
    def parse(cls, root):
        """
        Create a new AMDSec by parsing root.

        :param root: Element or ElementTree to be parsed into an object.
        """
        if root.tag != utils.lxmlns('mets') + 'amdSec':
            raise exceptions.ParseError('AMDSec can only parse amdSec elements with METS namespace.')
        section_id = root.get('ID')
        subsections = []
        for child in root:
            subsection = SubSection.parse(child)
            subsections.append(subsection)
        return cls(section_id, subsections)

    def serialize(self, now=None):
        """
        Serialize this amdSec and all children to lxml Element and return it.

        :param str now: Default value for CREATED in children if none set
        :return: amdSec Element with all children
        """
        el = etree.Element(utils.lxmlns('mets') + self.tag, ID=self.id_string())
        self.subsections.sort()
        for child in self.subsections:
            el.append(child.serialize(now))
        return el


class SubSection(object):
    """
    An object representing a metadata subsection in a document.

    This is usually created automatically and does not have to be instantiated directly.

    :param str subsection: Tag name for the subsection to be created.  Should be
        one of 'techMD', 'rightsMD', 'sourceMD' or 'digiprovMD' if contained in an
        :class:`amdSec`, or 'dmdSec'.
    :param contents: The MDWrap or MDRef contained in this subsection.
    :type contents: :class:`MDWrap` or :class:`MDRef`
    :param str section_id: ID of the section. If not provided, will be generated from subsection tag and a random number.
    """
    ALLOWED_SUBSECTIONS = ('techMD', 'rightsMD', 'sourceMD', 'digiprovMD', 'dmdSec')

    def __init__(self, subsection, contents, section_id=None):
        if subsection not in self.ALLOWED_SUBSECTIONS:
            raise ValueError(
                '%s must be one of %s' % (subsection, self.ALLOWED_SUBSECTIONS))
        self.subsection = subsection
        self.contents = contents
        self._id = section_id
        self.status = None
        self.older = None
        self.newer = None
        self.created = None

    def __lt__(self, other):
        # Sort based on the subsection's order in ALLOWED_SUBSECTIONS
        # techMDs < rightsMD < sourceMD < digiprovMD < dmdSec
        return self.ALLOWED_SUBSECTIONS.index(self.subsection) < self.ALLOWED_SUBSECTIONS.index(other.subsection)

    def id_string(self, force_generate=False):
        """
        Returns the ID string for this SubSection.

        :param bool force_generate: If True, will generate a new ID from the subsection tag and a random number.
        """
        if force_generate or not self._id:
            self._id = self.subsection + '_' + str(randint(1, 999999))
        return self._id

    def get_status(self):
        """
        Returns the STATUS when serializing.

        Calculates based on the subsection type and if it's replacing anything.

        :returns: None or the STATUS string.
        """
        if self.status:
            return self.status
        if self.subsection == 'dmdSec':
            if self.older is None:
                return 'original'
            else:
                return 'updated'
        if self.subsection == 'rightsMD':
            # TODO how to handle ones where newer has been deleted?
            if self.newer == None:
                return 'current'
            else:
                return 'superseded'
        return None

    def replace_with(self, new_subsection):
        """
        Replace this SubSection with new_subsection.

        Replacing SubSection must be the same time.  That is, you can only
        replace a dmdSec with another dmdSec, or a rightsMD with a rightsMD etc.

        :param new_subsection: Updated version of this SubSection
        :type new_subsection: :class:`SubSection`
        """
        if self.subsection != new_subsection.subsection:
            raise exceptions.MetsError('Must replace a SubSection with one of the same type.')
        # TODO convert this to a DB so have bidirectonal foreign keys??
        self.newer = new_subsection
        new_subsection.older = self
        self.status = None

    @classmethod
    def parse(cls, root):
        """
        Create a new SubSection by parsing root.

        :param root: Element or ElementTree to be parsed into an object.
        :raises exceptions.ParseError: If root's tag is not in :const:`SubSection.ALLOWED_SUBSECTIONS`.
        :raises exceptions.ParseError: If the first child of root is not mdRef or mdWrap.
        """
        subsection = root.tag.replace(utils.lxmlns('mets'), '', 1)
        if subsection not in cls.ALLOWED_SUBSECTIONS:
            raise exceptions.exceptions.ParseError('SubSection can only parse elements with tag in %s with METS namespace' % cls.ALLOWED_SUBSECTIONS)
        section_id = root.get('ID')
        created = root.get('CREATED')
        status = root.get('STATUS')
        child = root[0]
        if child.tag == utils.lxmlns('mets') + 'mdWrap':
            mdwrap = MDWrap.parse(child)
            obj = cls(subsection, mdwrap, section_id)
        elif child.tag == utils.lxmlns('mets') + 'mdRef':
            mdref = MDRef.parse(child)
            obj = cls(subsection, mdref, section_id)
        else:
            raise exceptions.exceptions.ParseError('Child of %s must be mdWrap or mdRef' % subsection)
        obj.created = created
        obj.status = status
        return obj

    def serialize(self, now=None):
        """
        Serialize this SubSection and all children to lxml Element and return it.

        :param str now: Default value for CREATED if none set
        :return: dmdSec/techMD/rightsMD/sourceMD/digiprovMD Element with all children
        """
        created = self.created or now
        el = etree.Element(utils.lxmlns('mets') + self.subsection, ID=self.id_string())
        if created:
            el.set('CREATED', created)
        status = self.get_status()
        if status:
            el.set('STATUS', status)
        if self.contents:
            el.append(self.contents.serialize())
        return el


class MDRef(object):
    """
    An object representing an external XML document, typically associated
    with an :class:`FSEntry` object.

    :param str target: Path to the external document. MDRef does not validate
        the existence of this target.
    :param str mdtype: The string representing the mdtype of XML document being
        enclosed. Examples include "PREMIS:OBJECT" and "PREMIS:EVENT".
    :param str label: Optional LABEL for the mdRef element
    :param str loctype: LOCTYPE of the mdRef.  Must be one of 'ARK', 'URN', 'URL', 'PURL', 'HANDLE', 'DOI' or 'OTHER'.
    :param str otherloctype: OTHERLOCTYPE of the mdRef. Should be provided if loctype is OTHER.
    """
    VALID_LOCTYPE = ('ARK', 'URN', 'URL', 'PURL', 'HANDLE', 'DOI', 'OTHER')

    def __init__(self, target, mdtype, loctype, label=None, otherloctype=None):
        self.target = target
        self.mdtype = mdtype
        self.loctype = loctype
        if loctype not in self.VALID_LOCTYPE:
            raise ValueError('loctype must be one of {}'.format(', '.join(self.VALID_LOCTYPE)))
        self.label = label
        self.otherloctype = otherloctype

    @classmethod
    def parse(cls, root):
        """
        Create a new MDWrap by parsing root.

        :param root: Element or ElementTree to be parsed into a MDWrap.
        """
        if root.tag != utils.lxmlns('mets') + 'mdRef':
            raise exceptions.ParseError('MDRef can only parse mdRef elements with METS namespace.')
        # Required attributes
        mdtype = root.get('MDTYPE')
        if not mdtype:
            raise exceptions.ParseError('mdRef must have a MDTYPE')
        target = root.get(utils.lxmlns('xlink') + 'href')
        if not target:
            raise exceptions.ParseError('mdRef must have an xlink:href.')
        loctype = root.get('LOCTYPE')
        if not loctype:
            raise exceptions.ParseError('mdRef must have a LOCTYPE')
        # Optional attributes
        label = root.get('LABEL')
        otherloctype = root.get('OTHERLOCTYPE')

        return cls(target, mdtype, loctype, label, otherloctype)

    def serialize(self):
        # If the source document is a METS document, the XPTR attribute of
        # this mdRef element should point to the IDs of each dmdSec element
        # in that document.
        XPTR = None
        try:
            target_doc = etree.parse(self.target)
            dmdsecs = [item.get('ID') for item in
                       target_doc.findall(utils.lxmlns('mets') + 'dmdSec')]
            XPTR = "xpointer(id(''))".format(' '.join(dmdsecs))
        except Exception:
            pass

        el = etree.Element(utils.lxmlns('mets') + 'mdRef')
        if self.label:
            el.attrib['LABEL'] = self.label
        if self.target:
            el.attrib[utils.lxmlns('xlink') + 'href'] = self.target
        el.attrib['MDTYPE'] = self.mdtype
        el.attrib['LOCTYPE'] = self.loctype
        if self.otherloctype:
            el.attrib['OTHERLOCTYPE'] = self.otherloctype
        if XPTR:
            el.attrib['XPTR'] = XPTR
        return el


class DublinCoreXmlData(object):
    """
    An object representing a METS xmlData element containing a Dublin Core element.

    :raises exceptions.ParseError: If the root element tag is not xmlData.
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
        :raises exceptions.ParseError: If the root is not xmlData or doesn't contain a dublincore element.
        """
        if root.tag != utils.lxmlns('mets') + 'xmlData':
            raise exceptions.ParseError('DublinCoreXmlData can only parse xmlData elements with mets namespace.')

        dc_el = root.find('dcterms:dublincore', namespaces=utils.NAMESPACES)

        if dc_el is None or dc_el.tag != utils.lxmlns('dcterms') + 'dublincore':
            raise exceptions.ParseError('xmlData can only contain a dublincore element with the dcterms namespace.')

        args = []

        for element in DublinCoreXmlData.DC_ELEMENTS:
            args.append(dc_el.findtext("dc:" + element, namespaces=utils.NAMESPACES))

        return cls(*args)

    def serialize(self):
        nsmap = OrderedDict([
            ('mets', utils.NAMESPACES['mets']),
            ('xsi', utils.NAMESPACES['xsi']),
            ('xlink', utils.NAMESPACES['xlink'])
        ])
        root = etree.Element(utils.lxmlns('mets') + 'xmlData', nsmap=nsmap)
        root.append(self._serialize_dublincore())
        return root

    def _serialize_dublincore(self):
        nsmap = OrderedDict([
            ('dcterms', utils.NAMESPACES['dcterms']),
            ('dc', utils.NAMESPACES['dc'])
        ])
        attrib = {'{}schemaLocation'.format(utils.lxmlns('xsi')): utils.DUBLINCORE_SCHEMA_LOCATIONS}
        dc_root = etree.Element(utils.lxmlns('dcterms') + 'dublincore', nsmap=nsmap, attrib=attrib)

        for element in DublinCoreXmlData.DC_ELEMENTS:
            dc_el = etree.Element(utils.lxmlns('dc') + element)
            dc_el.text = getattr(self, element)
            dc_root.append(dc_el)

        return dc_root


class MDWrap(object):
    """
    An object representing an XML document enclosed in a METS document.
    The entirety of the XML document will be included; to reference an
    external document, use the :class:`MDRef` class.

    :param str document: A string copy of the document, and will be parsed into
        an ElementTree at the time of instantiation.
    :param str mdtype: The MDTYPE of XML document being enclosed. Examples
        include "PREMIS:OBJECT" and "PREMIS:EVENT".
    """
    MDTYPE_CLASSES = {'DC': DublinCoreXmlData}

    def __init__(self, document, mdtype, data=None):
        parser = etree.XMLParser(remove_blank_text=True)
        if isinstance(document, six.string_types):
            self.document = etree.fromstring(document, parser=parser)
        elif isinstance(document, etree._Element):
            self.document = document
        self.mdtype = mdtype
        self.data = data

    @classmethod
    def parse(cls, root):
        """
        Create a new MDWrap by parsing root.

        :param root: Element or ElementTree to be parsed into a MDWrap.
        :raises exceptions.ParseError: If mdWrap does not contain MDTYPE
        :raises exceptions.ParseError: If mdWrap or xmlData contain multiple children
        """
        if root.tag != utils.lxmlns('mets') + 'mdWrap':
            raise exceptions.ParseError('MDWrap can only parse mdWrap elements with METS namespace.')
        mdtype = root.get('MDTYPE')
        if not mdtype:
            raise exceptions.ParseError('mdWrap must have a MDTYPE')
        if mdtype in MDWrap.MDTYPE_CLASSES.keys():
            mdtype_class = MDWrap.MDTYPE_CLASSES[mdtype]()
            data = mdtype_class.parse(root.find('mets:xmlData', namespaces=utils.NAMESPACES)).__dict__
        else:
            data = None

        document = root.xpath('mets:xmlData/*', namespaces=utils.NAMESPACES)
        if len(document) != 1:
            raise exceptions.ParseError('mdWrap and xmlData can only have one child')
        document = document[0]
        return cls(document, mdtype, data)

    def serialize(self):
        el = etree.Element(utils.lxmlns('mets') + 'mdWrap', MDTYPE=self.mdtype)
        xmldata = etree.SubElement(el, utils.lxmlns('mets') + 'xmlData')
        xmldata.append(self.document)

        return el
