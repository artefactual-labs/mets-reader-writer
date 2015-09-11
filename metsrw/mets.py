from __future__ import absolute_import

from datetime import datetime
import logging
from lxml import etree
import sys

# This package
from . import exceptions
from . import fsentry
from . import metadata
from . import utils

LOGGER = logging.getLogger(__name__)


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
            'xsi': utils.NAMESPACES['xsi'],
            'xlink': utils.NAMESPACES['xlink']
        }
        if fully_qualified:
            nsmap['mets'] = utils.NAMESPACES['mets']
        else:
            nsmap[None] = utils.NAMESPACES['mets']
        attrib = {
            '{}schemaLocation'.format(utils.lxmlns('xsi')):
            utils.SCHEMA_LOCATIONS
        }
        return etree.Element(utils.lxmlns('mets') + 'mets', nsmap=nsmap, attrib=attrib)

    def _mets_header(self, now):
        """
        Return the metsHdr Element.
        """
        if self.createdate is None:
            e = etree.Element(utils.lxmlns('mets') + 'metsHdr', CREATEDATE=now)
        else:
            e = etree.Element(utils.lxmlns('mets') + 'metsHdr',
                CREATEDATE=self.createdate, LASTMODDATE=now)
        return e

    def _collect_mdsec_elements(self, files):
        """
        Return all dmdSec and amdSec classes associated with the files.

        Returns all dmdSecs, then all amdSecs, so they only need to be
        serialized before being appended to the METS.

        :param List files: List of :class:`FSEntry` to collect MDSecs for.
        :returns: List of AMDSecs and SubSections
        """
        dmdsecs = []
        amdsecs = []
        for f in files:
            for d in f.dmdsecs:
                dmdsecs.append(d)
            for a in f.amdsecs:
                amdsecs.append(a)
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
        el = child.serialize_structmap()

        if parent is not None:
            parent.append(el)

        if child.children:
            for subchild in child.children:
                el.append(self._child_element(subchild, parent=el))

        return el

    def _structmap(self):
        structmap = etree.Element(utils.lxmlns('mets') + 'structMap', TYPE='physical',
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

        filesec = etree.Element(utils.lxmlns('mets') + 'fileSec')
        filegrps = {}
        for file_ in files:
            if file_.type != 'Item':
                continue
            # Get fileGrp, or create if not exist
            filegrp = filegrps.get(file_.use)
            if filegrp is None:
                filegrp = etree.SubElement(filesec, utils.lxmlns('mets') + 'fileGrp', USE=file_.use)
                filegrps[file_.use] = filegrp

            file_el = file_.serialize_filesec()
            if file_el is not None:
                filegrp.append(file_el)

        return filesec

    def serialize(self, fully_qualified=False):
        """
        Returns this document serialized to an xml Element.

        :return: Element for this document
        """
        now = datetime.utcnow().replace(microsecond=0).isoformat('T')
        files = self.all_files()
        mdsecs = self._collect_mdsec_elements(files)
        root = self._document_root(fully_qualified=fully_qualified)
        root.append(self._mets_header(now=now))
        for section in mdsecs:
            root.append(section.serialize(now=now))
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

    # PARSE HELPERS

    def _parse_tree_structmap(self, tree, parent_elem):
        """
        Recursively parse all the children of parent_elem, including amdSecs and dmdSecs.
        """
        siblings = []
        for elem in parent_elem:  # Iterates over children of parent_elem
            # Only handle div's, not fptrs
            if elem.tag != utils.lxmlns('mets') + 'div':
                continue
            entry_type = elem.get('TYPE')
            label = elem.get('LABEL')
            fptr = elem.find('mets:fptr', namespaces=utils.NAMESPACES)
            file_uuid = None
            derived_from = None
            use = None
            path = None
            amdids = None
            if fptr is not None:
                file_id = fptr.get('FILEID')
                file_elem = tree.find('mets:fileSec//mets:file[@ID="' + file_id + '"]', namespaces=utils.NAMESPACES)
                if file_elem is None:
                    raise exceptions.ParseError('%s exists in structMap but not fileSec' % file_id)
                file_uuid = file_id.replace(utils.FILE_ID_PREFIX, '', 1)
                group_uuid = file_elem.get('GROUPID').replace(utils.GROUP_ID_PREFIX, '', 1)
                if group_uuid != file_uuid:
                    derived_from = group_uuid  # Use group_uuid as placeholder
                use = file_elem.getparent().get('USE')
                path = file_elem.find('mets:FLocat', namespaces=utils.NAMESPACES).get(utils.lxmlns('xlink') + 'href')
                amdids = file_elem.get('ADMID')

            # Recursively generate children
            children = self._parse_tree_structmap(tree, elem)

            # Create FSEntry
            fs_entry = fsentry.FSEntry(path=path, label=label, use=use, type=entry_type, children=children, file_uuid=file_uuid, derived_from=derived_from)

            # Add DMDSecs
            dmdids = elem.get('DMDID')
            if dmdids:
                dmdids = dmdids.split()
                for dmdid in dmdids:
                    dmdsec_elem = tree.find('mets:dmdSec[@ID="' + dmdid + '"]', namespaces=utils.NAMESPACES)
                    dmdsec = metadata.SubSection.parse(dmdsec_elem)
                    fs_entry.dmdsecs.append(dmdsec)

            # Add AMDSecs
            if amdids:
                amdids = amdids.split()
                for amdid in amdids:
                    amdsec_elem = tree.find('mets:amdSec[@ID="' + amdid + '"]', namespaces=utils.NAMESPACES)
                    amdsec = metadata.AMDSec.parse(amdsec_elem)
                    fs_entry.amdsecs.append(amdsec)

            siblings.append(fs_entry)
        return siblings

    def _parse_tree(self, tree=None):
        if tree is None:
            tree = self.tree
        # self._validate()
        # Check CREATEDATE < now
        createdate = self.tree.find('mets:metsHdr', namespaces=utils.NAMESPACES).get('CREATEDATE')
        now = datetime.utcnow().isoformat('T')
        if createdate > now:
            raise exceptions.ParseError('CREATEDATE more recent than now (%s)' % now)
        self.createdate = createdate

        # Parse structMap
        structMap = tree.find('mets:structMap[@TYPE="physical"]', namespaces=utils.NAMESPACES)
        if structMap is None:
            raise exceptions.ParseError('No physical structMap found.')
        self._root_elements = self._parse_tree_structmap(tree, structMap)

        # Associated derived files
        for entry in self.all_files():
            # get_file will return None with parameter None
            entry.derived_from = self.get_file(entry.derived_from)

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


if __name__ == '__main__':
    mw = METSWriter()
    mw.fromfile(sys.argv[1])
    mw.write(sys.argv[2], fully_qualified=True, pretty_print=True)
