#!/usr/bin/python2 -OO

from datetime import datetime
from lxml import etree
import os
from random import randint
import sys


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
    return '{' + NAMESPACES[arg] + '}'


# CONSTANTS

FILE_ID_PREFIX = 'file-'
GROUP_ID_PREFIX = 'Group-'


# EXCEPTIONS

class MetsError(Exception):
    """ Base Exception for this module. """
    pass


class ParseError(MetsError):
    """ Error parsing a METS file. """
    pass


# CLASSES

class FSEntry(object):
    """
    A class representing a filesystem entry - either a file or a directory.

    When passed to a METSWriter instance, the tree of FSEntry objects will
    be used to construct the <fileSec> and <structMap> elements of a
    METS document.

    Unless otherwise specified, an FSEntry object is assumed to be a file;
    pass the `type` value as 'Directory' to specify that the object is
    instead a directory.

    An FSEntry object must be instantiated with a path as the first
    argument to the constructor, which represents its path on disk.

    An FSEntry object which is a Directory may have one or more children,
    representing files or directories contained within itself. Directory
    trees are designed for top-to-bottom traversal. Files cannot have
    children, and attempting to instantiate a file FSEntry object with
    children will raise a ValueError.

    Any FSEntry object may have one or more metadata entries associated
    with it; these can take the form of either references to other XML
    files on disk, which should be wrapped in MDRef objects, or
    wrapped copies of those XML files, which should be wrapped in
    MDWrap objects.

    :param str path: Path to the file on disk, as a bytestring. This will
        populate FLocat @xlink:href
    :param str label: Label in the structMap. If not provided, will be populated
        with the basename of path
    :param str use: Use for the fileGrp.  Items with identical uses will be
        grouped together.
    :param str type: Type of FSEntry this is. This will appear in the structMap.
    :param list children: List of :class:`FSEntry` that are direct children of
        this element in the structMap.  Only allowed if type is 'Directory'
    :param str file_uuid: UUID of this entry. Will be used to construct the
        FILEID used in the fileSec and structMap, and GROUPID.  Only required if
        type is 'Item'.
    :param FSEntry derived_from: FSEntry that this FSEntry is derived_from. This is used to set the GROUPID in the fileSec.
    :raises ValueError: if children passed when type is not 'Directory'
    """
    def __init__(self, path, label=None, use='original', type=u'Item', children=None, file_uuid=None, derived_from=None):
        # path can validly be any encoding; if this value needs
        # to be spliced later on, it's better to treat it as a
        # bytestring than as actually being encoded text.
        self.path = str(path)
        if label is None:
            label = os.path.basename(path)
        self.label = label
        self.use = use
        self.type = unicode(type)
        if children is None:
            children = []
        self.children = children
        self.file_uuid = file_uuid
        self.derived_from = derived_from
        self.amdsecs = []
        self.dmdsecs = []

        if type != 'Directory' and children:
            raise ValueError("Only directory objects can have children")

    def _create_id(self, prefix):
        return prefix + '_' + str(randint(1, 999999))

    def file_id(self):
        """ Returns the fptr FILEID if this is not a Directory. """
        if self.type == 'Directory':
            return None
        if self.file_uuid is None:
            raise MetsError('No FILEID: File %s does not have file_uuid set', self.path)
        return FILE_ID_PREFIX + self.file_uuid

    def group_id(self):
        """
        Returns the GROUPID.

        If derived_from is set, returns that group_id.
        """
        if self.derived_from is not None:
            return self.derived_from.group_id()
        if self.file_uuid is None:
            raise MetsError('No GROUPID: File %s does not have file_uuid set', self.path)
        return GROUP_ID_PREFIX + self.file_uuid

    def admids(self):
        """ Returns a list of ADMIDs for this entry. """
        return [a.id_string() for a in self.amdsecs]

    def dmdids(self):
        """ Returns a list of DMDIDs for this entry. """
        return [d.id_string() for d in self.dmdsecs]

    def _add_metadata_element(self, md, subsection, mdtype, mode='mdwrap'):
        """
        :param md: Value to pass to the MDWrap/MDRef
        :param str mdtype: Value for mdWrap/mdRef @MDTYPE
        :param str mode: 'mdwrap' or 'mdref'
        :param str subsection: Metadata tag to create.  See :const:`SubSection.ALLOWED_SUBSECTIONS`

        """
        # HELP how handle multiple amdSecs?
        # When adding *MD which amdSec to add to?
        if mode.lower() == 'mdwrap':
            mdsec = MDWrap(md, mdtype)
        elif mode.lower() == 'mdref':
            mdsec = MDRef(md, mdtype)
        subsection = SubSection(subsection, mdsec)
        if subsection.subsection == 'dmdSec':
            self.dmdsecs.append(subsection)
        else:
            try:
                amdsec = self.amdsecs[0]
            except IndexError:
                amdsec = AMDSec()
                self.amdsecs.append(amdsec)
            amdsec.subsections.append(subsection)
        return subsection

    def add_techmd(self, md, mdtype, mode='mdwrap'):
        return self._add_metadata_element(md, 'techMD', mdtype, mode)

    def add_digiprovmd(self, md, mdtype, mode='mdwrap'):
        return self._add_metadata_element(md, 'digiprovMD', mdtype, mode)

    def add_rightsmd(self, md, mdtype, mode='mdwrap'):
        return self._add_metadata_element(md, 'rightsMD', mdtype, mode)

    def add_dmdsec(self, md, mdtype, mode='mdwrap'):
        return self._add_metadata_element(md, 'dmdSec', mdtype, mode)

    def add_premis_object(self, md, mode='mdwrap'):
        # TODO add extra args and create PREMIS object here
        return self.add_techmd(md, 'PREMIS:OBJECT', mode)

    def add_premis_event(self, md, mode='mdwrap'):
        # TODO add extra args and create PREMIS object here
        return self.add_digiprovmd(md, 'PREMIS:EVENT', mode)

    def add_premis_agent(self, md, mode='mdwrap'):
        # TODO add extra args and create PREMIS object here
        return self.add_digiprovmd(md, 'PREMIS:AGENT', mode)

    def add_premis_rights(self, md, mode='mdwrap'):
        # TODO add extra args and create PREMIS object here
        return self.add_rightsmd(md, 'PREMIS:RIGHTS', mode)

    def add_dublin_core(self, md, mode='mdwrap'):
        # TODO add extra args and create DC object here
        return self.add_dmdsec(md, 'DC', mode)

    def add_child(self, child):
        if self.type != 'Directory':
            raise ValueError("Only directory objects can have children")
        self.children.append(child)


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

    @classmethod
    def parse(cls, root):
        """
        Create a new SubSection by parsing root.

        :param root: Element or ElementTree to be parsed into an object.
        :raises ParseError: If root's tag is not in :const:`SubSection.ALLOWED_SUBSECTIONS`.
        :raises ParseError: If the first child of root is not mdRef or mdWrap.
        """
        subsection = root.tag.replace(lxmlns('mets'), '', 1)
        if subsection not in cls.ALLOWED_SUBSECTIONS:
            raise ParseError('SubSection can only parse elements with tag in %s with METS namespace' % cls.ALLOWED_SUBSECTIONS)
        section_id = root.get('ID')
        child = root[0]
        if child.tag == lxmlns('mets') + 'mdWrap':
            mdwrap = MDWrap.parse(child)
            return cls(subsection, mdwrap, section_id)
        elif child.tag == lxmlns('mets') + 'mdRef':
            mdref = MDRef.parse(child)
            return cls(subsection, mdref, section_id)
        else:
            raise ParseError('Child of %s must be mdWrap or mdRef' % subsection)

    def serialize(self):
        el = etree.Element(lxmlns('mets') + self.subsection, ID=self.id_string())
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
    """
    def __init__(self, target, mdtype):
        self.target = target
        self.mdtype = mdtype

    @classmethod
    def parse(cls, root):
        """
        Create a new MDWrap by parsing root.

        :param root: Element or ElementTree to be parsed into a MDWrap.
        """
        if root.tag != lxmlns('mets') + 'mdRef':
            raise ParseError('MDRef can only parse mdRef elements with METS namespace.')
        mdtype = root.get('MDTYPE')
        if not mdtype:
            raise ParseError('mdRef must have a MDTYPE')
        target = root.get(lxmlns('xlink') + 'href')
        if not target:
            raise ParseError('mdRef must have an xlink:href.')
        return cls(target, mdtype)

    def serialize(self):
        # If the source document is a METS document, the XPTR attribute of
        # this mdRef element should point to the IDs of each dmdSec element
        # in that document.
        XPTR = None
        try:
            target_doc = etree.parse(self.target)
            dmdsecs = [item.get('ID') for item in
                       target_doc.findall(lxmlns('mets')+'dmdSec')]
            XPTR = "xpointer(id(''))".format(' '.join(dmdsecs))
        except Exception:
            pass

        attrib = {
            'LOCTYPE': 'URL',
            'OTHERLOCTYPE': 'SYSTEM',
            lxmlns('xlink')+'href': self.target,
            'MDTYPE': self.mdtype
        }
        if XPTR:
            attrib['XPTR'] = XPTR
        return etree.Element(lxmlns('mets') + 'mdRef', attrib=attrib)


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
    def __init__(self, document, mdtype):
        parser = etree.XMLParser(remove_blank_text=True)
        if isinstance(document, basestring):
            self.document = etree.fromstring(document, parser=parser)
        elif isinstance(document, etree._Element):
            self.document = document
        self.mdtype = mdtype

    @classmethod
    def parse(cls, root):
        """
        Create a new MDWrap by parsing root.

        :param root: Element or ElementTree to be parsed into a MDWrap.
        :raises ParseError: If mdWrap does not contain MDTYPE
        :raises ParseError: If mdWrap or xmlData contain multiple children
        """
        if root.tag != lxmlns('mets') + 'mdWrap':
            raise ParseError('MDWrap can only parse mdWrap elements with METS namespace.')
        mdtype = root.get('MDTYPE')
        if not mdtype:
            raise ParseError('mdWrap must have a MDTYPE')
        document = root.xpath('mets:xmlData/*',  namespaces=NAMESPACES)
        if len(document) != 1:
            raise ParseError('mdWrap and xmlData can only have one child')
        document = document[0]
        return cls(document, mdtype)

    def serialize(self):
        el = etree.Element(lxmlns('mets') + 'mdWrap', MDTYPE=self.mdtype)
        xmldata = etree.SubElement(el, lxmlns('mets') + 'xmlData')
        xmldata.append(self.document)

        return el


class AMDSec(object):
    """
    An object representing a section of administrative metadata in a
    document.

    This is ordinarily created by METSWriter instances and does not
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
        if root.tag != lxmlns('mets') + 'amdSec':
            raise ParseError('AMDSec can only parse amdSec elements with METS namespace.')
        section_id = root.get('ID')
        subsections = []
        for child in root:
            subsection = SubSection.parse(child)
            subsections.append(subsection)
        return cls(section_id, subsections)

    def serialize(self):
        el = etree.Element(lxmlns('mets') + self.tag, ID=self.id_string())
        self.subsections.sort()
        for child in self.subsections:
            el.append(child.serialize())
        return el


class METSWriter(object):
    def __init__(self):
        # Stores the ElementTree if this was parsed from an existing file
        self.tree = None
        # Only root-level elements are stored, since the rest
        # can be inferred via their #children attribute
        self.createdate = None
        self._root_elements = []
        self._all_files = None
        self._files_uuid = None
        self.dmdsecs = []
        self.amdsecs = []

    # FSENTRYS

    def _collect_all_files(self, files=None):
        """
        Collect all FSEntrys into a set, including all descendants.

        :param list files: List of :class:`FSEntry` to traverse.
        :returns: Set of FSEntry
        """
        if files is None:
            files = self._root_elements
        collected = set()
        for entry in files:
            collected.add(entry)
            collected.update(self._collect_all_files(entry.children))
        return collected

    def all_files(self):
        """
        Return a set of all FSEntrys in this METSWriter.

        :returns: Set containing all :class:`FSEntry` in this METSWriter,
            including descendants of ones explicitly added.
        """
        # NOTE: Cannot use _collect_files_uuid and .values() because not all
        # FSEntrys have UUIDs, and those without will be dropped.
        if not self._all_files:
            self._all_files = self._collect_all_files(self._root_elements)
        return self._all_files

    def _collect_files_uuid(self, files=None):
        """
        Collect all FSEntrys with UUIDs into a dict.

        :param list files: List of :class:`FSEntry` to traverse.
        :returns: Dict of {'uuid': FSEntry}
        """
        if files is None:
            files = self._root_elements
        collected = {}
        for entry in files:
            if entry.file_uuid is not None:
                collected[entry.file_uuid] = entry
            collected.update(self._collect_files_uuid(entry.children))
        return collected

    def get_file(self, file_uuid):
        """
        Return the FSEntry with file_uuid.

        :param str file_uuid: UUID of the FSEntry to fetch.
        :returns: :class:`FSEntry` with file_uuid.
        """
        if not self._files_uuid:
            self._files_uuid = self._collect_files_uuid(self._root_elements)
        return self._files_uuid.get(file_uuid)

    def append_file(self, fs_entry):
        """
        Adds an FSEntry object to this METS document's tree. Any of the
        represented object's children will also be added to the document.

        A given FSEntry object can only be included in a document once,
        and any attempt to add an object the second time will be ignored.

        :param FSEntry fs_entry: FSEntry to add to the METS file
        """

        if fs_entry in self._root_elements:
            return
        self._root_elements.append(fs_entry)
        # Reset file lists so they get regenerated with the new files(s)
        self._all_files = None
        self._files_uuid = None

    # SERIALIZE

    def _document_root(self, fully_qualified=False):
        """
        Return the mets Element for the document root.
        """
        nsmap = {
            'xsi': NAMESPACES['xsi'],
            'xlink': NAMESPACES['xlink']
        }
        if fully_qualified:
            nsmap['mets'] = NAMESPACES['mets']
        else:
            nsmap[None] = NAMESPACES['mets']
        attrib = {
            '{}schemaLocation'.format(lxmlns('xsi')):
            SCHEMA_LOCATIONS
        }
        return etree.Element(lxmlns('mets') + 'mets', nsmap=nsmap, attrib=attrib)

    def _mets_header(self):
        """
        Return the metsHdr Element.
        """
        date = datetime.utcnow().replace(microsecond=0).isoformat('T')
        if self.createdate is None:
            e = etree.Element(lxmlns('mets') + 'metsHdr', CREATEDATE=date)
        else:
            e = etree.Element(lxmlns('mets') + 'metsHdr',
                CREATEDATE=self.createdate, LASTMODDATE=date)
        return e

    def _collect_mdsec_elements(self, files):
        """
        Return all dmdSec and amdSec Element associated with the files.

        Returns all dmdSec Elements, then all amdSec Elements, suitable for
        immediately appending to the mets.

        :param list files: List of :class:`FSEntry` s to collect MDSecs for.
        """
        dmdsecs = []
        amdsecs = []
        for f in files:
            for d in f.dmdsecs:
                dmdsecs.append(d.serialize())
            for a in f.amdsecs:
                amdsecs.append(a.serialize())
        return dmdsecs + amdsecs

    def _child_element(self, child, parent=None):
        """
        Creates a <div> element suitable for use in a structMap from
        an FSEntry object. If the passed `child` represents a
        directory, its children will be recursively appended to itself.
        If the passed `child` represents a file, it will contain a
        <fptr> element.

        If the keyword argument `parent` is passed, the created element
        will be parented to that element. This is intended for
        use when recursing down a tree.
        """
        # TODO move this to FSEntry?
        el = etree.Element(lxmlns('mets') + 'div', TYPE=child.type, LABEL=child.label)
        if child.file_id():
            etree.SubElement(el, lxmlns('mets') + 'fptr', FILEID=child.file_id())
        dmdids = child.dmdids()
        if dmdids:
            el.set('DMDID', ' '.join(dmdids))

        if parent is not None:
            parent.append(el)

        if child.children:
            for subchild in child.children:
                el.append(self._child_element(subchild, parent=el))

        return el

    def _structmap(self):
        structmap = etree.Element(lxmlns('mets') + 'structMap', TYPE='physical',
                                  # TODO does it make sense that more
                                  # than one structmap might be generated?
                                  ID='structMap_1',
                                  # TODO don't hardcode this
                                  LABEL='Archivematica default')
        for item in self._root_elements:
            structmap.append(self._child_element(item))

        return structmap

    def _filesec(self, files=None):
        """
        Returns fileSec Element containing all files grouped by use.
        """
        if files is None:
            files = self.all_files()

        filesec = etree.Element(lxmlns('mets') + 'fileSec')
        filegrps = {}
        for file_ in files:
            if file_.type != 'Item':
                continue
            # Get fileGrp, or create if not exist
            filegrp = filegrps.get(file_.use)
            if filegrp is None:
                filegrp = etree.SubElement(filesec, lxmlns('mets') + 'fileGrp', USE=file_.use)
                filegrps[file_.use] = filegrp

            # TODO move this to the FSEntry?
            admids = file_.admids()
            file_el = etree.SubElement(filegrp, lxmlns('mets') + 'file', ID=file_.file_id(), GROUPID=file_.group_id())
            if admids:
                file_el.set('ADMID', ' '.join(admids))
            flocat = etree.SubElement(file_el, lxmlns('mets') + 'FLocat')
            # Setting manually so order is correct
            flocat.set(lxmlns('xlink')+'href', file_.path)
            flocat.set('LOCTYPE', 'OTHER')
            flocat.set('OTHERLOCTYPE', 'SYSTEM')

        return filesec

    def _parse_tree_structmap(self, tree, parent_elem):
        """
        Recursively parse all the children of parent_elem, including amdSecs and dmdSecs.
        """
        siblings = []
        for elem in parent_elem:  # Iterates over children of parent_elem
            # Only handle div's, not fptrs
            if elem.tag != lxmlns('mets') + 'div':
                continue
            entry_type = elem.get('TYPE')
            label = elem.get('LABEL')
            fptr = elem.find('mets:fptr', namespaces=NAMESPACES)
            file_uuid = None
            use = None
            path = None
            amdids = None
            if fptr is not None:
                file_id = fptr.get('FILEID')
                file_elem = tree.find('mets:fileSec//mets:file[@ID="' + file_id + '"]', namespaces=NAMESPACES)
                if file_elem is None:
                    raise ParseError('%s exists in structMap but not fileSec' % file_id)
                file_uuid = file_id.replace(FILE_ID_PREFIX, '', 1)
                use = file_elem.getparent().get('USE')
                path = file_elem.find('mets:FLocat', namespaces=NAMESPACES).get(lxmlns('xlink') + 'href')
                amdids = file_elem.get('ADMID')

            # Recursively generate children
            children = self._parse_tree_structmap(tree, elem)

            # Create FSEntry
            fsentry = FSEntry(path=path, label=label, use=use, type=entry_type, children=children, file_uuid=file_uuid)

            # Add DMDSecs
            dmdids = elem.get('DMDID')
            if dmdids:
                dmdids = dmdids.split()
                for dmdid in dmdids:
                    dmdsec_elem = tree.find('mets:dmdSec[@ID="' + dmdid + '"]', namespaces=NAMESPACES)
                    dmdsec = SubSection.parse(dmdsec_elem)
                    fsentry.dmdsecs.append(dmdsec)

            # Add AMDSecs
            if amdids:
                amdids = amdids.split()
                for amdid in amdids:
                    amdsec_elem = tree.find('mets:amdSec[@ID="' + amdid + '"]', namespaces=NAMESPACES)
                    amdsec = AMDSec.parse(amdsec_elem)
                    fsentry.amdsecs.append(amdsec)

            siblings.append(fsentry)
        return siblings

    def _parse_tree(self, tree=None):
        if tree is None:
            tree = self.tree
        # self._validate()
        # Check CREATEDATE < now
        createdate = self.tree.find('mets:metsHdr', namespaces=NAMESPACES).get('CREATEDATE')
        now = datetime.utcnow().isoformat('T')
        if createdate > now:
            raise ParseError('CREATEDATE more recent than now (%s)' % now)
        self.createdate = createdate

        # Parse structMap
        structMap = tree.find('mets:structMap[@TYPE="physical"]', namespaces=NAMESPACES)
        if structMap is None:
            raise ParseError('No physical structMap found.')
        self._root_elements = self._parse_tree_structmap(tree, structMap)

    def _validate(self):
        raise NotImplementedError()

    def fromfile(self, path):
        """
        Accept a filepath pointing to a valid METS file and parses it.

        :param str path: Path to a METS file.
        """
        parser = etree.XMLParser(remove_blank_text=True)
        self.tree = etree.parse(path, parser=parser)
        self._parse_tree(self.tree)

    def fromstring(self, string):
        """
        Accept a string containing valid METS xml and parses it.

        :param str string: String containing a METS file.
        """
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.fromstring(string, parser)
        self.tree = root.getroottree()
        self._parse_tree(self.tree)

    def fromtree(self, tree):
        """
        Accept an ElementTree or Element and parses it.

        :param ElementTree tree: ElementTree to build a METS file from.
        """
        self.tree = tree
        self._parse_tree(self.tree)

    def serialize(self, fully_qualified=False):
        """
        Returns this document serialized to an xml Element.

        :return: Element for this document
        """
        files = self.all_files()
        mdsecs = self._collect_mdsec_elements(files)
        root = self._document_root(fully_qualified=fully_qualified)
        root.append(self._mets_header())
        for el in mdsecs:
            root.append(el)
        root.append(self._filesec(files))
        root.append(self._structmap())

        return root

    def write(self, filepath, fully_qualified=False, pretty_print=False):
        """
        Serialize and write this METS file to `filepath`.

        :param str filepath: Path to write the METS to
        """
        root = self.serialize(fully_qualified=fully_qualified)
        tree = root.getroottree()
        tree.write(filepath, xml_declaration=True, pretty_print=pretty_print)


if __name__ == '__main__':
    mw = METSWriter()
    mw.fromfile(sys.argv[1])
    mw.write(sys.argv[2], fully_qualified=True, pretty_print=True)
