from __future__ import absolute_import

import logging
from lxml import etree
import os
from random import randint

import six

from . import exceptions
from .metadata import MDWrap, MDRef, SubSection, AMDSec
from . import utils

LOGGER = logging.getLogger(__name__)


class FSEntry(object):
    """
    A class representing a filesystem entry - either a file or a directory.

    When passed to a :class:`metsrw.mets.METSDocument` instance, the tree of FSEntry objects will
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
    :param str checksum: Value of the file's checksum. Required if checksumtype passed.
    :param str checksumtype: Type of the checksum. Must be one of :const:`FSEntry.ALLOWED_CHECKSUMS`.  Required if checksum passed.
    :raises ValueError: if children passed when type is not 'Directory'
    :raises ValueError: if only one of checksum or checksumtype passed
    :raises ValueError: if checksumtype is not in :const:`FSEntry.ALLOWED_CHECKSUMS`
    """

    ALLOWED_CHECKSUMS = ('Adler-32', 'CRC32', 'HAVAL', 'MD5', 'MNP', 'SHA-1', 'SHA-256', 'SHA-384', 'SHA-512', 'TIGER WHIRLPOOL')

    def __init__(self, path=None, label=None, use='original', type=u'Item', children=None, file_uuid=None, derived_from=None, checksum=None, checksumtype=None):
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
        """
        Add a child FSEntry to this FSEntry.

        Only FSEntrys with a type of 'directory' can have children.

        This does not detect cyclic parent/child relationships, but that will cause problems.

        :param FSEntry child: FSEntry to add as a child
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
        if self.type.lower() != 'item' or self.use is None:
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
            flocat.set(utils.lxmlns('xlink') + 'href', self.path)
            flocat.set('LOCTYPE', 'OTHER')
            flocat.set('OTHERLOCTYPE', 'SYSTEM')

        return el

    def serialize_structmap(self, recurse=True):
        """
        Return the div Element for this file, appropriate for use in a structMap.

        If this FSEntry represents a directory, its children will be recursively appended to itself.
        If this FSEntry represents a file, it will contain a <fptr> element.

        :param bool recurse: If true, serialize and apppend all children.  Otherwise, only serialize this element but not any children.
        :return: structMap element for this FSEntry
        """
        if not self.label:
            return None
        el = etree.Element(utils.lxmlns('mets') + 'div', TYPE=self.type, LABEL=self.label)
        if self.file_id():
            etree.SubElement(el, utils.lxmlns('mets') + 'fptr', FILEID=self.file_id())
        if self.dmdids:
            el.set('DMDID', ' '.join(self.dmdids))

        if recurse and self._children:
            for child in self._children:
                child_el = child.serialize_structmap(recurse=recurse)
                if child_el is not None:
                    el.append(child_el)

        return el
