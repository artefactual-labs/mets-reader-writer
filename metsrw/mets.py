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


class METSDocument(object):
    def __init__(self):
        # Stores the ElementTree if this was parsed from an existing file
        self.tree = None
        # Only root-level elements are stored, since the rest
        # can be inferred via their #children attribute
        self.createdate = None
        self._root_elements = []
        self._all_files = None
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
        Return a set of all FSEntrys in this METS document.

        :returns: Set containing all :class:`FSEntry` in this METS document,
            including descendants of ones explicitly added.
        """
        # FIXME cache this. Should not break when add_child is called on an element already in the document.
        return self._collect_all_files(self._root_elements)

    def get_file(self, **kwargs):
        """
        Return the FSEntry that matches parameters.

        :param str file_uuid: UUID of the target FSEntry.
        :param str label: structMap LABEL of the target FSEntry.
        :param str type: structMap TYPE of the target FSEntry.
        :returns: :class:`FSEntry` that matches parameters, or None.
        """
        # TODO put this in a sqlite DB so it can be queried efficiently
        # TODO handle multiple matches (with DB?)
        # TODO check that kwargs are actual attrs
        for entry in self.all_files():
            if all(value == getattr(entry, key) for key, value in kwargs.items()):
                return entry
        return None

    def append_file(self, fs_entry):
        """
        Adds an FSEntry object to this METS document's tree. Any of the
        represented object's children will also be added to the document.

        A given FSEntry object can only be included in a document once,
        and any attempt to add an object the second time will be ignored.

        :param FSEntry fs_entry: FSEntry to add to the METS document
        """

        if fs_entry in self._root_elements:
            return
        self._root_elements.append(fs_entry)
        # Reset file lists so they get regenerated with the new files(s)
        self._all_files = None

    def remove_entry(self, fs_entry):
        """
        Removes an FSEntry object from this METS document.

        Any children of this FSEntry will also be removed. This will be removed as a child of it's parent, if any.

        :param FSEntry fs_entry: FSEntry to remove from the METS
        """
        try:
            self._root_elements.remove(fs_entry)
        except ValueError:  # fs_entry may not be in the root elements
            pass
        if fs_entry.parent:
            fs_entry.parent.remove_child(fs_entry)
        # Reset file lists so they get regenerated without the removed file(s)
        self._all_files = None


    # SERIALIZE

    def _document_root(self, fully_qualified=True):
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
        serialized before being appended to the METS document.

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

        dmdsecs.sort(key=lambda x: x.id_string())
        amdsecs.sort(key=lambda x: x.id_string())
        return dmdsecs + amdsecs

    def _structmap(self):
        """
        Returns structMap element for all files.
        """
        structmap = etree.Element(utils.lxmlns('mets') + 'structMap',
                                  TYPE='physical',
                                  # TODO Add ability for multiple structMaps
                                  ID='structMap_1',
                                  # TODO don't hardcode this
                                  LABEL='Archivematica default')
        for item in self._root_elements:
            child = item.serialize_structmap(recurse=True)
            if child is not None:
                structmap.append(child)

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
            if file_.type.lower() != 'item':
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

    def serialize(self, fully_qualified=True):
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

    def tostring(self, fully_qualified=True, pretty_print=True):
        """
        Serialize and return a string of this METS document.

        To write to file, see :meth:`write`

        :return: String of this document
        """
        root = self.serialize(fully_qualified=fully_qualified)
        return etree.tostring(root, pretty_print=pretty_print, xml_declaration=True)

    def write(self, filepath, fully_qualified=True, pretty_print=False):
        """
        Serialize and write this METS document to `filepath`.

        :param str filepath: Path to write the METS document to
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
            file_uuid = derived_from = use = path = amdids = checksum = checksumtype = None
            if fptr is not None:
                file_id = fptr.get('FILEID')
                file_elem = tree.find('mets:fileSec//mets:file[@ID="' + file_id + '"]', namespaces=utils.NAMESPACES)
                if file_elem is None:
                    raise exceptions.ParseError('%s exists in structMap but not fileSec' % file_id)
                file_uuid = file_id.replace(utils.FILE_ID_PREFIX, '', 1)
                group_uuid = file_elem.get('GROUPID', '').replace(utils.GROUP_ID_PREFIX, '', 1)
                if group_uuid != file_uuid:
                    derived_from = group_uuid  # Use group_uuid as placeholder
                use = file_elem.getparent().get('USE')
                path = file_elem.find('mets:FLocat', namespaces=utils.NAMESPACES).get(utils.lxmlns('xlink') + 'href')
                amdids = file_elem.get('ADMID')
                checksum = file_elem.get('CHECKSUM')
                checksumtype = file_elem.get('CHECKSUMTYPE')

            # Recursively generate children
            children = self._parse_tree_structmap(tree, elem)

            # Create FSEntry
            fs_entry = fsentry.FSEntry(path=path, label=label, use=use, type=entry_type, children=children, file_uuid=file_uuid, derived_from=derived_from, checksum=checksum, checksumtype=checksumtype)

            # Add DMDSecs
            dmdids = elem.get('DMDID')
            if dmdids:
                dmdids = dmdids.split()
                for dmdid in dmdids:
                    dmdsec_elem = tree.find('mets:dmdSec[@ID="' + dmdid + '"]', namespaces=utils.NAMESPACES)
                    dmdsec = metadata.SubSection.parse(dmdsec_elem)
                    fs_entry.dmdsecs.append(dmdsec)
                # Create older/newer relationships
                fs_entry.dmdsecs.sort(key=lambda x: x.created)
                for prev_dmdsec, dmdsec in zip(fs_entry.dmdsecs, fs_entry.dmdsecs[1:]):
                    if dmdsec.status == 'updated':
                        prev_dmdsec.replace_with(dmdsec)

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
        if createdate and createdate > now:
            raise exceptions.ParseError('CREATEDATE more recent than now (%s)' % now)
        self.createdate = createdate

        # Parse structMap
        structMap = tree.find('mets:structMap[@TYPE="physical"]', namespaces=utils.NAMESPACES)
        if structMap is None:
            raise exceptions.ParseError('No physical structMap found.')
        self._root_elements = self._parse_tree_structmap(tree, structMap)

        # Associated derived files
        for entry in self.all_files():
            entry.derived_from = self.get_file(file_uuid=entry.derived_from, type='Item')

    def _validate(self):
        raise NotImplementedError()

    def _fromfile(self, path):
        """
        Accept a filepath pointing to a valid METS document and parses it.

        :param str path: Path to a METS document.
        """
        parser = etree.XMLParser(remove_blank_text=True)
        self.tree = etree.parse(path, parser=parser)
        self._parse_tree(self.tree)

    @classmethod
    def fromfile(klass, path):
        """ Creates a METS by parsing a file. """
        i = klass()
        i._fromfile(path)
        return i

    def _fromstring(self, string):
        """
        Accept a string containing valid METS xml and parses it.

        :param str string: String containing a METS document.
        """
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.fromstring(string, parser)
        self.tree = root.getroottree()
        self._parse_tree(self.tree)

    @classmethod
    def fromstring(klass, string):
        """ Create a METS by parsing a string. """
        i = klass()
        i._fromstring(string)
        return i

    def _fromtree(self, tree):
        """
        Accept an ElementTree or Element and parses it.

        :param ElementTree tree: ElementTree to build a METS document from.
        """
        self.tree = tree
        self._parse_tree(self.tree)

    @classmethod
    def fromtree(klass, tree):
        """ Create a METS from an ElementTree or Element. """
        i = klass()
        i._fromtree(tree)
        return i

if __name__ == '__main__':
    mw = METSDocument()
    mw.fromfile(sys.argv[1])
    mw.write(sys.argv[2], fully_qualified=True, pretty_print=True)
