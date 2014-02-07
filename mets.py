from datetime import datetime
from random import randint

from lxml import etree


NAMESPACES = {
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "mets": "http://www.loc.gov/METS/",
    "premis": "info:lc/xmlns/premis-v2",
    "dcterms": "http://purl.org/dc/terms/",
    "fits": "http://hul.harvard.edu/ois/xml/ns/fits/fits_output",
    "xlink": "http://www.w3.org/1999/xlink",
    "dc": "http://purl.org/dc/elements/1.1/"
}

# These are convenience copies to allow wrapping the namespaces
# in lxml's format without confusing extra curly braces
# in string literals.
LXML_NAMESPACES = {
    "dc": "{" + NAMESPACES['dc'] + "}",
    "dcterms": "{" + NAMESPACES['dcterms'] + "}",
    "xsi": "{" + NAMESPACES['xsi'] + "}",
    "mets": "{" + NAMESPACES['mets'] + "}",
    "premis": "{" + NAMESPACES['premis'] + "}",
    "fits": "{" + NAMESPACES['fits'] + "}",
    "xlink": "{" + NAMESPACES['xlink'] + "}"
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
    MDWrap objects. These can be appended using one of the following
    methods:

    add_techmd(md, type, mode)     - technical metadata
    add_digiprovmd(md, type, mode) - digital provenance metadata
    """
    def __init__(self, path, children=[], type=u'file',
                 use='original', id=None):
        # path can validly be any encoding; if this value needs
        # to be spliced later on, it's better to treat it as a
        # bytestring than as actually being encoded text.
        self.path = str(path)
        self.type = unicode(type)
        self.use = use
        self.id = id
        self.children = children
        self.amdsecs = []
        self.dmdsecs = []

        if type == 'file' and children:
            raise Exception("Only directory objects can have children")

    def _create_id(self, prefix):
        return prefix + '_' + str(randint(1, 999999))

    # TODO This probably needs to be far more flexible and support more than
    # just techMD and digiProvMD types.
    def _add_metadata_element(self, md, type, mode='mdwrap', category=None):
        if mode == 'mdwrap':
            mdsec = MDWrap(md, type)
        elif mode == 'mdref':
            mdsec = MDSec(md, type)
        md_element = etree.Element(category, ID=self._create_id(category))
        md_element.append(mdsec.serialize())
        if category == 'techMD':
            self.amdsecs.append(AMDSec(md_element, category))
        elif category == 'digiProvMD':
            self.dmdsecs.append(DMDSec(md_element, category))

    def add_techmd(self, md, type, mode=None):
        self._add_metadata_element(md, type, mode, category='techMD')

    def add_digiprovmd(self, md, type, mode='mdwrap'):
        self._add_metadata_element(md, type, mode, category='digiProvMD')


class MDRef(object):
    """
    An object representing an external XML document, typically associated
    with an FSEntry object.

    The `target` attribute is a path to the external document. MDRef does
    not validate the existence of this target.

    The `type` argument must be a string representing the type of XML
    document being enclosed. Examples include "PREMIS:OBJECT" and
    "PREMIS:EVENT".
    """
    def __init__(self, target, type):
        self.target = target
        self.type = type
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
            'MDTYPE': self.type
        }
        if XPTR:
            attrib['XPTR'] = XPTR
        return etree.Element('mdRef', attrib=attrib)


class MDWrap(object):
    """
    An object representing an XML document enclosed in a METS document.
    The entirety of the XML document will be included; to reference an
    external document, use the MDRef class.

    The `document` argument must contain a string copy of the document,
    and will be parsed into an ElementTree at the time of instantiation.

    The `type` argument must be a string representing the type of XML
    document being enclosed. Examples include "PREMIS:OBJECT" and
    "PREMIS:EVENT".
    """
    def __init__(self, document, type):
        parser = etree.XMLParser(remove_blank_text=True)
        self.document = etree.fromstring(document, parser=parser)
        self.type = type
        self.id = None

    def serialize(self):
        el = etree.Element('mdWrap', MDTYPE=self.type)
        xmldata = etree.SubElement(el, 'xmlData')
        xmldata.append(self.document)

        return el


class MDSec(object):
    type = None

    def __init__(self, contents, type):
        self.contents = contents
        self.type = type
        self.number = str(randint(1, 999999))

    def id_string(self):
        # e.g., amdSec_1
        return self.__class__.type + '_' + self.number

    def serialize(self):
        el = etree.Element(self.__class__.type, ID=self.id_string())
        el.append(self.contents)

        return el


class AMDSec(MDSec):
    """
    An object representing a section of administrative metadata in a
    document.

    This is ordinarily created by METSWriter instances and does not
    have to be instantiated directly.
    """

    type = 'amdSec'


class DMDSec(MDSec):
    """
    An object representing a section of descriptive metadata in a
    document.

    This is ordinarily created by METSWriter instances and does not
    have to be instantiated directly.
    """

    type = 'dmdSec'


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
        self.tree = etree.ElementTree()
        # Only root-level elements are stored, since the rest
        # can be inferred via their #children attribute
        self.root_elements = []
        self.dmdsecs = []
        self.amdsecs = []

    def _document_root(self):
        attrib = {
            '{}schemaLocation'.format(lxmlns('xsi')):
            SCHEMA_LOCATIONS
        }
        return etree.Element('mets', nsmap=NSMAP, attrib=attrib)

    def _mets_header(self):
        date = datetime.utcnow().isoformat('T')
        return etree.Element('metsHdr', CREATEDATE=date)

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
            fileid = child.id
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

    def append_file(self, file):
        """
        Adds an FSEntry object to this METS document's tree. Any of the
        represented object's children will also be added to the document.

        A given FSEntry object can only be included in a document once,
        and any attempt to add an object the second time will be ignored.
        """

        if file in self.root_elements:
            return

        self.root_elements.append(file)
        self._append_file_properties(file)

        # children are *not* included in the root properties list,
        # because anything that includes children will already
        # allow traversal down the tree.
        # However, we *do* require the full set of mdSecs at this time.
        for child in file.children:
            self._append_file_properties(child)

    def serialize(self):
        """
        Returns an ElementTree object representing this document.
        """
        root = self._document_root()
        root.append(self._mets_header())
        for el in self._mdsec_elements():
            root.append(el)
        root.append(self._filesec().serialize())
        root.append(self._structmap())

        return root
