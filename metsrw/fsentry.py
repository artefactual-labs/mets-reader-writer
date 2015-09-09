import os
from random import randint

import exceptions
from metadata import MDWrap, MDRef, SubSection, AMDSec
import utils


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
            raise exceptions.MetsError('No FILEID: File %s does not have file_uuid set' % self.path)
        return utils.FILE_ID_PREFIX + self.file_uuid

    def group_id(self):
        """
        Returns the GROUPID.

        If derived_from is set, returns that group_id.
        """
        if self.derived_from is not None:
            return self.derived_from.group_id()
        if self.file_uuid is None:
            raise exceptions.MetsError('No GROUPID: File %s does not have file_uuid set' % self.path)
        return utils.GROUP_ID_PREFIX + self.file_uuid

    def admids(self):
        """ Returns a list of ADMIDs for this entry. """
        return [a.id_string() for a in self.amdsecs]

    def dmdids(self):
        """ Returns a list of DMDIDs for this entry. """
        return [d.id_string() for d in self.dmdsecs]

    def _add_metadata_element(self, md, subsection, mdtype, mode='mdwrap', **kwargs):
        """
        :param md: Value to pass to the MDWrap/MDRef
        :param str subsection: Metadata tag to create.  See :const:`SubSection.ALLOWED_SUBSECTIONS`
        :param str mdtype: Value for mdWrap/mdRef @MDTYPE
        :param str mode: 'mdwrap' or 'mdref'
        :param str loctype: Required if mode is 'mdref'. LOCTYPE of a mdRef
        :param str label: Optional. Label of a mdRef
        :param str otherloctype: Optional. OTHERLOCTYPE of a mdRef.

        """
        # HELP how handle multiple amdSecs?
        # When adding *MD which amdSec to add to?
        if mode.lower() == 'mdwrap':
            mdsec = MDWrap(md, mdtype)
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
        if self.type != 'Directory':
            raise ValueError("Only directory objects can have children")
        self.children.append(child)