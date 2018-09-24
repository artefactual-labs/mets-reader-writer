# -*- coding: utf-8 -*-
from __future__ import absolute_import

from itertools import chain
import logging
import os
from random import randint

from lxml import etree
import six

from .di import (
    is_class,
    has_methods,
    has_class_methods,
    Dependency,
    DependencyPossessor,
)
from . import exceptions
from .metadata import MDWrap, MDRef, SubSection, AMDSec
from . import utils

LOGGER = logging.getLogger(__name__)


class FSEntry(DependencyPossessor):
    """A class representing a filesystem entry - either a file or a directory.

    When passed to a :class:`metsrw.mets.METSDocument` instance, the tree of
    FSEntry objects will be used to construct the <fileSec> and <structMap>
    elements of a METS document.

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
    :param list children: List of :class:`metsrw.fsentry.FSEntry` that are
        direct children of this element in the structMap.  Only allowed if type
        is 'Directory'
    :param str file_uuid: UUID of this entry. Will be used to construct the
        FILEID used in the fileSec and structMap, and GROUPID.  Only required if
        type is 'Item'.
    :param metsrw.fsentry.FSEntry derived_from: FSEntry that this FSEntry is
        derived_from. This is used to set the GROUPID in the fileSec.
    :param str checksum: Value of the file's checksum. Required if checksumtype passed.
    :param str checksumtype: Type of the checksum. Must be one of
        :const:`FSEntry.ALLOWED_CHECKSUMS`.  Required if checksum passed.
    :param list transform_files: a list of dicts representing METS transform
        file elements, which provide "a means to access any subsidiary files
        listed below a <file> element by indicating the steps required to
        'unpack' or transform the subsidiary files."
    :raises ValueError: if children passed when type is not 'Directory'
    :raises ValueError: if only one of checksum or checksumtype passed
    :raises ValueError: if checksumtype is not in :const:`FSEntry.ALLOWED_CHECKSUMS`
    """

    ALLOWED_CHECKSUMS = ('Adler-32', 'CRC32', 'HAVAL', 'MD5', 'MNP', 'SHA-1', 'SHA-256', 'SHA-384', 'SHA-512', 'TIGER WHIRLPOOL')

    # Dependencies that must be injected. This means that an
    # ``FSEntry`` instance must be able to call ``self.premis_object_class`` and
    # get a class with methods ``fromtree`` and ``serialize``.
    premis_object_class = Dependency(
        has_methods('serialize'),
        has_class_methods('fromtree'),
        is_class)
    premis_event_class = Dependency(
        has_methods('serialize'),
        has_class_methods('fromtree'),
        is_class)
    premis_agent_class = Dependency(
        has_methods('serialize'),
        has_class_methods('fromtree'),
        is_class)

    PREMIS_OBJECT = 'PREMIS:OBJECT'
    PREMIS_EVENT = 'PREMIS:EVENT'
    PREMIS_AGENT = 'PREMIS:AGENT'

    def __init__(self, path=None, label=None, use='original', type=u'Item',
                 children=None, file_uuid=None, derived_from=None,
                 checksum=None, checksumtype=None, transform_files=None,
                 mets_div_type=None):
        # path can validly be any encoding; if this value needs
        # to be spliced later on, it's better to treat it as a
        # bytestring than as actually being encoded text.
        # TODO update this with six and bytes
        if path:
            path = str(path)
        self.path = path
        if label is None and path is not None:
            label = os.path.basename(path)
        self.label = label
        self.use = use
        self.type = six.text_type(type)
        self.parent = None
        self._children = []
        if not transform_files:
            transform_files = []
        self.transform_files = transform_files
        self.mets_div_type = mets_div_type or self.type
        children = children or []
        for child in children:
            self.add_child(child)
        self.file_uuid = file_uuid
        self.derived_from = derived_from
        if bool(checksum) != bool(checksumtype):
            raise ValueError("Must provide both checksum and checksumtype, or neither. Provided values: %s and %s" % (checksum, checksumtype))
        if checksumtype and checksumtype not in self.ALLOWED_CHECKSUMS:
            raise ValueError(
                '%s must be one of %s' % (checksumtype, self.ALLOWED_CHECKSUMS))
        self.checksum = checksum
        self.checksumtype = checksumtype
        self.amdsecs = []
        self.dmdsecs = []

    def __str__(self):
        return '{s.type}: {s.path}'.format(s=self)

    def __repr__(self):
        return 'FSEntry(type={s.type!r}, path={s.path!r}, use={s.use!r}, label={s.label!r}, file_uuid={s.file_uuid!r}, checksum={s.checksum!r}, checksumtype={s.checksumtype!r})'.format(s=self)

    # PROPERTIES

    def _create_id(self, prefix):
        return prefix + '_' + str(randint(1, 999999))

    def file_id(self):
        """ Returns the fptr @FILEID if this is not a Directory. """
        if self.type.lower() == 'directory':
            return None
        if self.file_uuid is None:
            raise exceptions.MetsError('No FILEID: File %s does not have file_uuid set' % self.path)
        if self.is_aip:
            return os.path.splitext(os.path.basename(self.path))[0]
        return utils.FILE_ID_PREFIX + self.file_uuid

    def group_id(self):
        """
        Returns the @GROUPID.

        If derived_from is set, returns that group_id.
        """
        if self.derived_from is not None:
            return self.derived_from.group_id()
        if self.file_uuid is None:
            return None
        return utils.GROUP_ID_PREFIX + self.file_uuid

    @property
    def admids(self):
        """ Returns a list of ADMIDs for this entry. """
        return [a.id_string() for a in self.amdsecs]

    @property
    def dmdids(self):
        """ Returns a list of DMDIDs for this entry. """
        return [d.id_string() for d in self.dmdsecs]

    @property
    def children(self):
        # Read-only
        return self._children

    @property
    def is_aip(self):
        return self.type.lower() == 'archival information package'

    # ADD ATTRIBUTES

    def _add_metadata_element(self, md, subsection, mdtype, mode='mdwrap', **kwargs):
        """
        :param md: Value to pass to the MDWrap/MDRef
        :param str subsection: Metadata tag to create.  See :const:`SubSection.ALLOWED_SUBSECTIONS`
        :param str mdtype: Value for mdWrap/mdRef @MDTYPE
        :param str mode: 'mdwrap' or 'mdref'
        :param str loctype: Required if mode is 'mdref'. LOCTYPE of a mdRef
        :param str label: Optional. Label of a mdRef
        :param str otherloctype: Optional. OTHERLOCTYPE of a mdRef.
        :param str othermdtype: Optional. OTHERMDTYPE of a mdWrap.

        """
        # HELP how handle multiple amdSecs?
        # When adding *MD which amdSec to add to?
        if mode.lower() == 'mdwrap':
            othermdtype = kwargs.get('othermdtype')
            mdsec = MDWrap(md, mdtype, othermdtype)
        elif mode.lower() == 'mdref':
            loctype = kwargs.get('loctype')
            label = kwargs.get('label')
            otherloctype = kwargs.get('otherloctype')
            mdsec = MDRef(md, mdtype, loctype, label, otherloctype)
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

    def add_techmd(self, md, mdtype, mode='mdwrap', **kwargs):
        return self._add_metadata_element(md, 'techMD', mdtype, mode, **kwargs)

    def add_digiprovmd(self, md, mdtype, mode='mdwrap', **kwargs):
        return self._add_metadata_element(md, 'digiprovMD', mdtype, mode, **kwargs)

    def add_rightsmd(self, md, mdtype, mode='mdwrap', **kwargs):
        return self._add_metadata_element(md, 'rightsMD', mdtype, mode, **kwargs)

    def add_dmdsec(self, md, mdtype, mode='mdwrap', **kwargs):
        return self._add_metadata_element(md, 'dmdSec', mdtype, mode, **kwargs)

    def serialize_md_inst(self, md_inst, md_class):
        """Serialize object ``md_inst`` by transforming it into an
        ``lxml.etree._ElementTree``. If it already is such, return it. If not,
        make sure it is the correct type and return the output of calling
        ``seriaize()`` on it.
        """
        valid_insts = tuple(
            chain((etree._ElementTree, etree._Element), six.string_types))
        if isinstance(md_inst, valid_insts):
            return md_inst
        if not isinstance(md_inst, md_class):
            raise TypeError(
                'Instance {!r} must be instance of {!r}'.format(
                    md_inst, md_class))
        return md_inst.serialize()

    def add_premis_object(self, md, mode='mdwrap'):
        meth = self.add_techmd
        if self.is_empty_dir:
            meth = self.add_dmdsec
        return meth(
            self.serialize_md_inst(md, self.premis_object_class),
            self.PREMIS_OBJECT, mode)

    def add_premis_event(self, md, mode='mdwrap'):
        return self.add_digiprovmd(
            self.serialize_md_inst(md, self.premis_event_class),
            self.PREMIS_EVENT, mode)

    def add_premis_agent(self, md, mode='mdwrap'):
        return self.add_digiprovmd(
            self.serialize_md_inst(md, self.premis_agent_class),
            self.PREMIS_AGENT, mode)

    def add_premis_rights(self, md, mode='mdwrap'):
        # TODO add extra args and create PREMIS object here
        return self.add_rightsmd(md, 'PREMIS:RIGHTS', mode)

    def add_dublin_core(self, md, mode='mdwrap'):
        # TODO add extra args and create DC object here
        return self.add_dmdsec(md, 'DC', mode)

    def add_child(self, child):
        """Add a child FSEntry to this FSEntry.

        Only FSEntrys with a type of 'directory' can have children.

        This does not detect cyclic parent/child relationships, but that will
        cause problems.

        :param metsrw.fsentry.FSEntry child: FSEntry to add as a child
        :return: The newly added child
        :raises ValueError: If this FSEntry cannot have children.
        :raises ValueError: If the child and the parent are the same
        """
        if self.type.lower() != 'directory':
            raise ValueError("Only directory objects can have children")
        if child is self:
            raise ValueError('Cannot be a child of itself!')
        if child not in self._children:
            self._children.append(child)
        child.parent = self
        return child

    def remove_child(self, child):
        """
        Remove a child from this FSEntry

        If `child` is not actually a child of this entry, nothing happens.

        :param child: Child to remove
        """
        try:
            self._children.remove(child)
        except ValueError:  # Child may not be in list
            pass
        else:
            child.parent = None

    # SERIALIZE

    def serialize_filesec(self):
        """
        Return the file Element for this file, appropriate for use in a fileSec.

        If this is not an Item or has no use, return None.

        :return: fileSec element for this FSEntry
        """
        if self.type.lower() not in ('item', 'archival information package') or self.use is None:
            return None
        el = etree.Element(utils.lxmlns('mets') + 'file', ID=self.file_id())
        if self.group_id():
            el.attrib['GROUPID'] = self.group_id()
        if self.admids:
            el.set('ADMID', ' '.join(self.admids))
        if self.checksum and self.checksumtype:
            el.attrib['CHECKSUM'] = self.checksum
            el.attrib['CHECKSUMTYPE'] = self.checksumtype
        if self.path:
            flocat = etree.SubElement(el, utils.lxmlns('mets') + 'FLocat')
            # Setting manually so order is correct
            flocat.set(
                utils.lxmlns('xlink') + 'href', utils.urlencode(self.path))
            flocat.set('LOCTYPE', 'OTHER')
            flocat.set('OTHERLOCTYPE', 'SYSTEM')
        for transform_file in self.transform_files:
            transform_file_el = etree.SubElement(
                el, utils.lxmlns('mets') + 'transformFile')
            for key, val in transform_file.items():
                attribute = 'transform{}'.format(key).upper()
                transform_file_el.attrib[attribute] = str(val)
        return el

    @property
    def is_empty_dir(self):
        """Returns ``True`` if this fs item is a directory with no children or
        a directory with only other empty directories as children.
        """
        if self.mets_div_type == 'Directory':
            children = self._children
            if children:
                if all(child.is_empty_dir for child in children):
                    return True
                else:
                    return False
            else:
                return True
        else:
            return False

    def serialize_structmap(self, recurse=True, normative=False):
        """Return the div Element for this file, appropriate for use in a
        structMap.

        If this FSEntry represents a directory, its children will be
        recursively appended to itself. If this FSEntry represents a file, it
        will contain a <fptr> element.

        :param bool recurse: If true, serialize and apppend all children.
            Otherwise, only serialize this element but not any children.
        :param bool normative: If true, we are creating a "Normative Directory
            Structure" logical structmap, in which case we add div elements for
            empty directories and do not add fptr elements for files.
        :return: structMap element for this FSEntry
        """
        if not self.label:
            return None
        # Empty directories are not included in the physical structmap.
        if self.is_empty_dir and not normative:
            return None
        el = etree.Element(utils.lxmlns('mets') + 'div',
                           TYPE=self.mets_div_type)
        el.attrib['LABEL'] = self.label
        if (not normative) and self.file_id():
            etree.SubElement(el, utils.lxmlns('mets') + 'fptr',
                             FILEID=self.file_id())
        if self.dmdids:
            if (not normative) or (normative and self.is_empty_dir):
                el.set('DMDID', ' '.join(self.dmdids))
        if recurse and self._children:
            for child in self._children:
                child_el = child.serialize_structmap(
                    recurse=recurse, normative=normative)
                if child_el is not None:
                    el.append(child_el)
        return el

    def get_subsections_of_type(self, mdtype, md_class):
        try:
            return [md_class.fromtree(ss.contents.document)
                    for ss in self.amdsecs[0].subsections
                    if ss.contents.mdtype == mdtype]
        except IndexError:
            return []

    def get_premis_objects(self):
        return self.get_subsections_of_type(
            self.PREMIS_OBJECT, self.premis_object_class)

    def get_premis_events(self):
        return self.get_subsections_of_type(
            self.PREMIS_EVENT, self.premis_event_class)

    def get_premis_agents(self):
        return self.get_subsections_of_type(
            self.PREMIS_AGENT, self.premis_agent_class)

    def get_premis_event(self, event_uuid):
        try:
            return [evt for evt in self.get_premis_events()
                    if evt.identifier_value == event_uuid][0]
        except IndexError:
            return None
