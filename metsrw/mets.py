# -*- coding: utf-8 -*-
from __future__ import absolute_import

from builtins import object
from collections import OrderedDict, namedtuple
from datetime import datetime
import logging
import os
import six
import sys

from lxml import etree

# This package
from . import exceptions
from . import fsentry
from . import metadata
from . import utils


LOGGER = logging.getLogger(__name__)

AIP_ENTRY_TYPE = 'archival information package'
FPtr = namedtuple(
    'FPtr', 'file_uuid derived_from use path amdids checksum checksumtype')


class METSDocument(object):

    def __init__(self):
        # Stores the ElementTree if this was parsed from an existing file
        self.tree = None
        # Only root-level elements are stored, since the rest
        # can be inferred via their #children attribute
        self.createdate = None
        self._root_elements = []
        self._all_files = None
        self._iter = None
        self.dmdsecs = []
        self.amdsecs = []

    @classmethod
    def read(cls, source):
        """Read ``source`` into a ``METSDocument`` instance. This is an
        instance constructor. The ``source`` may be a path to a METS file, a
        file-like object, or a string of XML.
        """
        if hasattr(source, 'read'):
            return cls.fromfile(source)
        if os.path.exists(source):
            return cls.fromfile(source)
        if isinstance(source, six.string_types):
            source = source.encode('utf8')
        return cls.fromstring(source)

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
        # FIXME cache this. Should not break when add_child is called on an
        # element already in the document.
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
            if all(value == getattr(entry, key)
                   for key, value in kwargs.items()):
                return entry
        return None

    def append_file(self, fs_entry):
        """
        Adds an FSEntry object to this METS document's tree. Any of the
        represented object's children will also be added to the document.

        A given FSEntry object can only be included in a document once,
        and any attempt to add an object the second time will be ignored.

        :param metsrw.mets.FSEntry fs_entry: FSEntry to add to the METS document
        """

        if fs_entry in self._root_elements:
            return
        self._root_elements.append(fs_entry)
        # Reset file lists so they get regenerated with the new files(s)
        self._all_files = None

    append = append_file

    def remove_entry(self, fs_entry):
        """Removes an FSEntry object from this METS document.

        Any children of this FSEntry will also be removed. This will be removed
        as a child of it's parent, if any.

        :param metsrw.mets.FSEntry fs_entry: FSEntry to remove from the METS
        """
        try:
            self._root_elements.remove(fs_entry)
        except ValueError:  # fs_entry may not be in the root elements
            pass
        if fs_entry.parent:
            fs_entry.parent.remove_child(fs_entry)
        # Reset file lists so they get regenerated without the removed file(s)
        self._all_files = None

    remove = remove_entry

    # The following methods allow us to iterate over the FSEntry instances of a
    # METSDocument---``for fsentry in mets: ...``---, count
    # them---``len(mets)``---, and fetch them by
    # index---``my_fsentry = mets[21]``.

    def __iter__(self):
        return self

    def __len__(self):
        return len(self.all_files())

    def _get_all_files_list(self):
        return sorted(self.all_files(), key=lambda fsentry: fsentry.path or '')

    def __getitem__(self, index):
        return self._get_all_files_list()[index]

    def __next__(self):      # Py3-style iterator interface
        if self._iter is None:
            self._iter = iter(self._get_all_files_list())
        return next(self._iter)

    # SERIALIZE

    @staticmethod
    def _document_root(fully_qualified=True):
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

    @staticmethod
    def _collect_mdsec_elements(files):
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

    def _normative_structmap(self):
        """Returns the normative structMap element for all files. This is a
        logical structMap that includes empty directories.
        """
        structmap = etree.Element(utils.lxmlns('mets') + 'structMap',
                                  TYPE='logical',
                                  ID='structMap_2',
                                  LABEL='Normative Directory Structure')
        for item in self._root_elements:
            child = item.serialize_structmap(recurse=True, normative=True)
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
            if file_.type.lower() not in ('item', AIP_ENTRY_TYPE):
                continue
            # Get fileGrp, or create if not exist
            filegrp = filegrps.get(file_.use)
            if filegrp is None:
                filegrp = etree.SubElement(
                    filesec, utils.lxmlns('mets') + 'fileGrp', USE=file_.use)
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
        root.append(self._normative_structmap())
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
        """Serialize and write this METS document to `filepath`.

        :param str filepath: Path to write the METS document to
        """
        root = self.serialize(fully_qualified=fully_qualified)
        tree = root.getroottree()
        tree.write(filepath, xml_declaration=True, pretty_print=pretty_print)

    # PARSE HELPERS

    def _parse_tree_structmap(self, tree, parent_elem,
                              normative_parent_elem=None):
        """Recursively parse all the children of parent_elem, including amdSecs
        and dmdSecs.
        :param lxml._ElementTree tree: encodes the entire METS file.
        :param lxml._Element parent_elem: the element whose children we are
            parsing.
        :param lxml._Element normative_parent_elem: the normative
            counterpart of ``parent_elem`` taken from the logical structMap
            labelled "Normative Directory Structure".
        """
        siblings = []
        el_to_normative = self._get_el_to_normative(
            parent_elem, normative_parent_elem)
        for elem, normative_elem in el_to_normative.items():
            if elem.tag != utils.lxmlns('mets') + 'div':
                continue  # Only handle divs, not fptrs
            entry_type = elem.get('TYPE')
            label = elem.get('LABEL')
            fptr = self._analyze_fptr(elem, tree, entry_type)
            children = self._parse_tree_structmap(
                tree, elem, normative_parent_elem=normative_elem)
            fs_entry = fsentry.FSEntry(
                path=fptr.path, label=label, use=fptr.use, type=entry_type,
                children=children, file_uuid=fptr.file_uuid,
                derived_from=fptr.derived_from, checksum=fptr.checksum,
                checksumtype=fptr.checksumtype)
            self._add_dmdsecs_to_fs_entry(elem, fs_entry, tree)
            self._add_amdsecs_to_fs_entry(fptr.amdids, fs_entry, tree)
            siblings.append(fs_entry)
        return siblings

    @staticmethod
    def _get_el_to_normative(parent_elem, normative_parent_elem):
        """Return ordered dict ``el_to_normative``, which maps children of
        ``parent_elem`` to their normative counterparts in the children of
        ``normative_parent_elem`` or to ``None`` if there is no normative
        parent. If there is a normative div element with no non-normative
        counterpart, that element is treated as a key with value ``None``.
        This allows us to create ``FSEntry`` instances for empty directory div
        elements, which are only documented in a normative logical structmap.
        """
        el_to_normative = OrderedDict()
        if normative_parent_elem is None:
            for el in parent_elem:
                el_to_normative[el] = None
        else:
            for norm_el in normative_parent_elem:
                matches = [el for el in parent_elem
                           if el.get('TYPE') == norm_el.get('TYPE') and
                           el.get('LABEL') == norm_el.get('LABEL')]
                if matches:
                    el_to_normative[matches[0]] = norm_el
                else:
                    el_to_normative[norm_el] = None
        return el_to_normative

    @staticmethod
    def _analyze_fptr(elem, tree, entry_type):
        fptr = elem.find('mets:fptr', namespaces=utils.NAMESPACES)
        if fptr is None:
            return FPtr(*[None] * 7)
        else:
            file_uuid = derived_from = use = path = amdids = checksum = \
                checksumtype = None
            file_id = fptr.get('FILEID')
            file_elem = tree.find(
                'mets:fileSec//mets:file[@ID="' + file_id + '"]',
                namespaces=utils.NAMESPACES)
            if file_elem is None:
                raise exceptions.ParseError(
                    '%s exists in structMap but not fileSec' % file_id)
            use = file_elem.getparent().get('USE')
            path = file_elem.find(
                'mets:FLocat', namespaces=utils.NAMESPACES).get(
                    utils.lxmlns('xlink') + 'href')
            amdids = file_elem.get('ADMID')
            checksum = file_elem.get('CHECKSUM')
            checksumtype = file_elem.get('CHECKSUMTYPE')
            file_id_prefix = utils.FILE_ID_PREFIX
            # If the file is an AIP, then its prefix is not "file-" but the
            # name of the AIP. Therefore we need to get the extension-less
            # basename of the AIP's path and remove its UUID suffix to ge
            # the prefix to remove from the FILEID attribute value.
            if entry_type.lower() == 'archival information package':
                file_id_prefix = os.path.splitext(
                    os.path.basename(path))[0][:-36]
            file_uuid = file_id.replace(file_id_prefix, '', 1)
            group_uuid = file_elem.get('GROUPID', '').replace(
                utils.GROUP_ID_PREFIX, '', 1)
            if group_uuid != file_uuid:
                derived_from = group_uuid  # Use group_uuid as placeholder
            return FPtr(file_uuid, derived_from, use, path, amdids,
                        checksum, checksumtype)

    @staticmethod
    def _add_dmdsecs_to_fs_entry(elem, fs_entry, tree):
        dmdids = elem.get('DMDID')
        if dmdids:
            dmdids = dmdids.split()
            for dmdid in dmdids:
                dmdsec_elem = tree.find('mets:dmdSec[@ID="' + dmdid + '"]',
                                        namespaces=utils.NAMESPACES)
                dmdsec = metadata.SubSection.parse(dmdsec_elem)
                fs_entry.dmdsecs.append(dmdsec)
            # Create older/newer relationships
            fs_entry.dmdsecs.sort(key=lambda x: x.created)
            for prev_dmdsec, dmdsec in zip(
                    fs_entry.dmdsecs, fs_entry.dmdsecs[1:]):
                if dmdsec.status == 'updated':
                    prev_dmdsec.replace_with(dmdsec)

    @staticmethod
    def _add_amdsecs_to_fs_entry(amdids, fs_entry, tree):
        if amdids:
            amdids = amdids.split()
            for amdid in amdids:
                amdsec_elem = tree.find(
                    'mets:amdSec[@ID="' + amdid + '"]',
                    namespaces=utils.NAMESPACES)
                amdsec = metadata.AMDSec.parse(amdsec_elem)
                fs_entry.amdsecs.append(amdsec)

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
        structMap = tree.find('mets:structMap[@TYPE="physical"]',
                              namespaces=utils.NAMESPACES)
        if structMap is None:
            raise exceptions.ParseError('No physical structMap found.')
        normative_struct_map = tree.find(
            'mets:structMap[@TYPE="logical"]'
            '[@LABEL="Normative Directory Structure"]',
            namespaces=utils.NAMESPACES)
        self._root_elements = self._parse_tree_structmap(
            tree, structMap, normative_parent_elem=normative_struct_map)

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
    def fromfile(cls, path):
        """ Creates a METS by parsing a file. """
        i = cls()
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
    def fromstring(cls, string):
        """ Create a METS by parsing a string. """
        i = cls()
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
    def fromtree(cls, tree):
        """ Create a METS from an ElementTree or Element. """
        i = cls()
        i._fromtree(tree)
        return i


if __name__ == '__main__':
    mw = METSDocument()
    mw.fromfile(sys.argv[1])
    mw.write(sys.argv[2], fully_qualified=True, pretty_print=True)
