from datetime import datetime
import os
from random import randint
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

NSMAP = {
    None: NAMESPACES['mets'],
    'dc': NAMESPACES['dcterms'],
    'xsi': NAMESPACES['xsi'],
    'xlink': NAMESPACES['xlink']
}

SCHEMA_LOCATIONS = "http://www.loc.gov/METS/ " + \
                   "http://www.loc.gov/standards/mets/version18/mets.xsd"


def lxmlns(arg):
    return '{' + NAMESPACES[arg] + '}'


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
    :param str file_id: ID of this entry. Will be used in the fileSec and
        structMap.  Only required if type is 'Item'
    :raises ValueError: if children passed when type is not 'Directory'
    """
    def __init__(self, path, label=None, use='original', type=u'Item', children=[], file_id=None):
        # path can validly be any encoding; if this value needs
        # to be spliced later on, it's better to treat it as a
        # bytestring than as actually being encoded text.
        self.path = str(path)
        if label is None:
            label = os.path.basename(path)
        self.label = label
        self.type = unicode(type)
        self.use = use
        self.file_id = file_id
        self.children = children
        self.amdsecs = []
        self.dmdsecs = []

        if type != 'Directory' and children:
            raise ValueError("Only directory objects can have children")

    def _create_id(self, prefix):
        return prefix + '_' + str(randint(1, 999999))

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
            mdsec = MDSec(md, mdtype)
        subsection = SubSection(subsection, mdsec)
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


class SubSection(object):
    """
    An object representing a metadata subsection in a document.

    This is usually created automatically and does not have to be instantiated directly.

    :param str subsection: Tag name for the subsection to be created.  Should be
        one of 'techMD', 'rightsMD', 'sourceMD' or 'digiprovMD' if contained in an
        :class:`amdSec`, or 'dmdSec'.
    :param contents: The MDWrap or MDRef contained in this subsection.
    :type contents: :class:`MDWrap` or :class:`MDRef`
    """
    ALLOWED_SUBSECTIONS = ('techMD', 'rightsMD', 'sourceMD', 'digiprovMD', 'dmdSec')

    def __init__(self, subsection, contents):
        if subsection not in self.ALLOWED_SUBSECTIONS:
            raise ValueError(
                '%s must be one of %s' % (subsection, self.ALLOWED_SUBSECTIONS))
        self.subsection = subsection
        self.contents = contents
        self._id = None

    def __lt__(self, other):
        # Sort based on the subsection's order in ALLOWED_SUBSECTIONS
        # techMDs < rightsMD < sourceMD < digiprovMD < dmdSec
        return self.ALLOWED_SUBSECTIONS.index(self.subsection) < self.ALLOWED_SUBSECTIONS.index(other.subsection)

    def id_string(self, force_generate=False):
        if force_generate or not self._id:
            self._id = self.subsection + '_' + str(randint(1, 999999))
        return self._id

    def serialize(self):
        el = etree.Element(self.subsection, ID=self.id_string())
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
        self.id = None

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
        except:
            pass

        attrib = {
            'LOCTYPE': 'URL',
            'OTHERLOCTYPE': 'SYSTEM',
            lxmlns('xlink')+'href': self.target,
            'MDTYPE': self.mdtype
        }
        if XPTR:
            attrib['XPTR'] = XPTR
        return etree.Element('mdRef', attrib=attrib)


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
        self.document = etree.fromstring(document, parser=parser)
        self.mdtype = mdtype
        self.id = None

    def serialize(self):
        el = etree.Element('mdWrap', MDTYPE=self.mdtype)
        xmldata = etree.SubElement(el, 'xmlData')
        xmldata.append(self.document)

        return el


class MDSec(object):
    tag = None

    def __init__(self):
        self.subsections = []
        self._id = None

    def id_string(self, force_generate=False):
        # e.g., amdSec_1
        if force_generate or not self._id:
            self._id = self.tag + '_' + str(randint(1, 999999))
        return self._id

    def serialize(self):
        el = etree.Element(self.tag, ID=self.id_string())
        self.subsections.sort()
        for child in self.subsections:
            el.append(child.serialize())
        return el


class AMDSec(MDSec):
    """
    An object representing a section of administrative metadata in a
    document.

    This is ordinarily created by METSWriter instances and does not
    have to be instantiated directly.
    """

    tag = 'amdSec'


class DMDSec(MDSec):
    """
    An object representing a section of descriptive metadata in a
    document.

    This is ordinarily created by METSWriter instances and does not
    have to be instantiated directly.
    """

    tag = 'dmdSec'


class METSWriter(object):
    def __init__(self):
        # Stores the ElementTree if this was parsed from an existing file
        self.tree = None
        # Only root-level elements are stored, since the rest
        # can be inferred via their #children attribute
        self.createdate = None
        self.root_elements = []
        self.dmdsecs = []
        self.amdsecs = []

    def _document_root(self):
        """
        Return the mets Element for the document root.
        """
        attrib = {
            '{}schemaLocation'.format(lxmlns('xsi')):
            SCHEMA_LOCATIONS
        }
        return etree.Element('mets', nsmap=NSMAP, attrib=attrib)

    def _mets_header(self):
        """
        Return the metsHdr Element.
        """
        date = datetime.utcnow().isoformat('T')
        if self.createdate is None:
            e = etree.Element('metsHdr', CREATEDATE=date)
        else:
            e = etree.Element('metsHdr',
                CREATEDATE=self.createdate, LASTMODDATE=date)
        return e

    def _collect_files(self, files=None):
        """
        Collect all FSEntrys into a flat list, including all descendants.

        :param list files: List of :class:`FSEntry` to traverse.
        """
        if files is None:
            files = self.root_elements
        collected = set()
        for entry in files:
            collected.add(entry)
            collected.update(self._collect_files(entry.children))
        return collected

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
        el = etree.Element('div', TYPE=child.type, LABEL=child.label)
        if child.file_id:
            etree.SubElement(el, 'fptr', FILEID=child.file_id)

        if parent is not None:
            parent.append(el)

        if child.children:
            for subchild in child.children:
                el.append(self._child_element(subchild, parent=el))

        return el

    def _structmap(self):
        structmap = etree.Element('structMap', TYPE='physical',
                                  # TODO does it make sense that more
                                  # than one structmap might be generated?
                                  ID='structMap_1',
                                  # TODO don't hardcode this
                                  LABEL='Archivematica default')
        for item in self.root_elements:
            structmap.append(self._child_element(item))

        return structmap

    def _filesec(self, files=None):
        """
        Returns fileSec Element containing all files grouped by use.
        """
        if files is None:
            files = self._collect_files()

        filesec = etree.Element('fileSec')
        # TODO GROUPID
        filegrps = {}
        for file_ in files:
            if file_.type != 'Item':
                continue
            # Get fileGrp, or create if not exist
            filegrp = filegrps.get(file_.use)
            if filegrp is None:
                filegrp = etree.SubElement(filesec, 'fileGrp', USE=file_.use)
                filegrps[file_.use] = filegrp

            # TODO move this to the FSEntry?
            admids = file_.admids()
            file_el = etree.SubElement(filegrp, 'file', ID=file_.file_id)
            if admids:
                file_el.set('ADMID', ' '.join(admids))
            attrib = {
                lxmlns('xlink')+'href': file_.path,
                'LOCTYPE': 'OTHER',
                'OTHERLOCTYPE': 'SYSTEM'
            }
            etree.SubElement(file_el, 'FLocat', attrib=attrib)

        return filesec

    def _parse_tree(self):
        # self._validate()
        # Check CREATEDATE < now
        createdate = self.tree.find('mets:metsHdr', namespaces=NAMESPACES).get('CREATEDATE')
        now = datetime.utcnow().isoformat('T')
        if createdate > now:
            raise ParseError('CREATEDATE more recent than now (%s)' % now)
        self.createdate = createdate

    def _validate(self):
        raise NotImplementedError()

    def fromfile(self, path):
        """
        Accept a filepath pointing to a valid METS file and parses it.

        :param str path: Path to a METS file.
        """
        self.tree = etree.parse(path)
        self._parse_tree()

    def fromstring(self, string):
        """
        Accept a string containing valid METS xml and parses it.

        :param str string: String containing a METS file.
        """
        root = etree.fromstring(string)
        self.tree = root.getroottree()
        self._parse_tree()

    def fromtree(self, tree):
        """
        Accept an ElementTree or Element and parses it.

        :param ElementTree tree: ElementTree to build a METS file from.
        """
        self.tree = tree
        self._parse_tree()

    def append_file(self, fs_entry):
        """
        Adds an FSEntry object to this METS document's tree. Any of the
        represented object's children will also be added to the document.

        A given FSEntry object can only be included in a document once,
        and any attempt to add an object the second time will be ignored.

        :param FSEntry fs_entry: FSEntry to add to the METS file
        """

        if fs_entry in self.root_elements:
            return
        self.root_elements.append(fs_entry)

    def serialize(self):
        """
        Returns this document serialized to an xml Element.

        :return: Element for this document
        """
        files = self._collect_files()
        mdsecs = self._collect_mdsec_elements(files)
        root = self._document_root()
        root.append(self._mets_header())
        for el in mdsecs:
            root.append(el)
        root.append(self._filesec())
        root.append(self._structmap())

        return root

    def write(self, filepath, pretty_print=False):
        """
        Serialize and write this METS file to `filepath`.

        :param str filepath: Path to write the METS to
        """
        root = self.serialize()
        tree = root.getroottree()
        tree.write(filepath, xml_declaration=True, pretty_print=pretty_print)
