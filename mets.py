from datetime import datetime
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


def flatten_list(l):
    new = []
    for item in l:
        if isinstance(item, list):
            new.extend(flatten_list(item))
        else:
            new.append(item)

    return new


class FSEntry(object):
    """
    A class representing a filesystem entry - either a file or a directory.
    Unless otherwise specified, an FSEntry object is assumed to be a file;
    pass the `type` value as 'directory' to specify that the object is
    instead a directory.

    When passed to a METSWriter instance, the tree of FSEntry objects will
    be used to construct the <fileSec> and <structMap> elements of a
    METS document.

    An FSEntry object must be instantiated with a path as the first
    argument to the constructor, which represents its path on disk.

    An FSEntry object which is a directory may have one or more children,
    representing files or directories contained within itself. Directory
    trees are designed for top-to-bottom traversal. Files cannot have
    children, and attempting to instantiate a file FSEntry object with
    children will raise an Exception.

    Any FSEntry object may have one or more metadata entries associated
    with it; these can take the form of either references to other XML
    files on disk, which should be wrapped in MDRef objects, or
    wrapped copies of those XML files, which should be wrapped in
    MDWrap objects.
    """
    def __init__(self, path, children=[], type=u'file',
                 use='original', file_id=None):
        # path can validly be any encoding; if this value needs
        # to be spliced later on, it's better to treat it as a
        # bytestring than as actually being encoded text.
        self.path = str(path)
        self.type = unicode(type)
        self.use = use
        self.file_id = file_id
        self.children = children
        self.amdsecs = []
        self.dmdsecs = []

        if type == 'file' and children:
            raise Exception("Only directory objects can have children")

    def _create_id(self, prefix):
        return prefix + '_' + str(randint(1, 999999))

    # TODO This probably needs to be far more flexible and support more than
    # just techMD and digiprovMD types.
    def _add_metadata_element(self, md, type, mode='mdwrap', category=None):
        if mode == 'mdwrap':
            mdsec = MDWrap(md, type)
        elif mode == 'mdref':
            mdsec = MDSec(md, type)
        md_element = etree.Element(category, ID=self._create_id(category))
        md_element.append(mdsec.serialize())
        if category == 'techMD':
            self.amdsecs.append(AMDSec(md_element, md_type=category))
        elif category == 'digiprovMD':
            self.dmdsecs.append(DMDSec(md_element, md_type=category))

    def add_techmd(self, md, type, mode=None):
        self._add_metadata_element(md, type, mode, category='techMD')

    def add_digiprovmd(self, md, type, mode='mdwrap'):
        self._add_metadata_element(md, type, mode, category='digiprovMD')


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

    def __init__(self, contents, md_type):

        self.contents = contents
        self.md_type = md_type
        self.number = str(randint(1, 999999))

    def id_string(self):
        # e.g., amdSec_1
        return self.tag + '_' + self.number

    def serialize(self):
        el = etree.Element(self.tag, ID=self.id_string())
        el.append(self.contents)

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


class FileSec(object):
    def __init__(self, files):
        self.files = files

    def serialize(self):
        el = etree.Element('fileSec')
        filegrp = etree.SubElement(el, 'fileGrp', USE='original')
        # TODO ID? GROUPID? ADMID? DMDID?
        for file_ in flatten_list(self.files):
            file_el = etree.SubElement(filegrp, 'file', ID=file_.id)
            attrib = {
                lxmlns('xlink')+'href': file_.path,
                'LOCTYPE': 'OTHER',
                'OTHERLOCTYPE': 'SYSTEM'
            }
            etree.SubElement(file_el, 'FLocat', attrib=attrib)

        return el


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
        if child.type == 'file':
            type = 'Item'
            fileid = child.file_id
        else:
            type = 'Directory'
            fileid = None

        el = etree.Element('div', TYPE=type, LABEL=child.path)
        if fileid:
            etree.SubElement(el, 'fptr', FILEID=fileid)

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

    def _recursive_files(self, files=None):
        """
        Returns a recursive list of all files in the document,
        including all children of the referenced files.

        If called with no arguments, begins with self.root_elements.
        """
        if files is None:
            files = self.root_elements

        file_list = []
        for file_ in files:
            file_list.append([file_])
            if file_.children:
                file_list.append(self._recursive_files(file_.children))

        return file_list

    def _filesec(self):
        return FileSec(self._recursive_files())

    def _append_file_properties(self, file):
        for amdsec in file.amdsecs:
            self.amdsecs.append(amdsec)
        for dmdsec in file.dmdsecs:
            self.dmdsecs.append(dmdsec)

    def _mdsec_elements(self):
        elements = []
        for amdsec in self.amdsecs:
            elements.append(amdsec.serialize())
        for dmdsec in self.dmdsecs:
            elements.append(dmdsec.serialize())

        return elements

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
        self._append_file_properties(fs_entry)

        # children are *not* included in the root properties list,
        # because anything that includes children will already
        # allow traversal down the tree.
        # However, we *do* require the full set of mdSecs at this time.
        for child in fs_entry.children:
            self._append_file_properties(child)

    def serialize(self):
        """
        Returns this document serialized to an xml Element.

        :return: Element for this document
        """
        root = self._document_root()
        root.append(self._mets_header())
        for el in self._mdsec_elements():
            root.append(el)
        root.append(self._filesec().serialize())
        root.append(self._structmap())

        return root

    def write(self, filepath):
        """
        Serialize and write this METS file to `filepath`.

        :param str filepath: Path to write the METS to
        """
        root = self.serialize()
        tree = root.getroottree()
        tree.write(filepath, xml_declaration=True)
