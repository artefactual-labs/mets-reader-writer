# -*- coding: utf-8 -*-

import pytest
from unittest import TestCase
import uuid
import six

import metsrw


class TestFSEntry(TestCase):
    """ Test FSEntry class. """

    @pytest.mark.skipif(six.PY3, reason="metsrw still uses Unicode in python3")
    def test_path_is_binary(self):
        """It should store the ``path`` as a bytestring."""
        sample = u"💜🎑💜"
        assert isinstance(
            metsrw.FSEntry(sample, type="Directory").path, six.binary_type
        )
        assert isinstance(
            metsrw.FSEntry(sample.encode("utf-8"), type="Directory").path,
            six.binary_type,
        )

    def test_create_invalid_checksum_type(self):
        """ It should only accept METS valid checksum types. """
        metsrw.FSEntry("file[1].txt", checksumtype="Adler-32", checksum="dummy")
        metsrw.FSEntry("file[1].txt", checksumtype="CRC32", checksum="dummy")
        metsrw.FSEntry("file[1].txt", checksumtype="HAVAL", checksum="dummy")
        metsrw.FSEntry(
            "file[1].txt",
            checksumtype="MD5",
            checksum="daa05c683a4913b268653f7a7e36a5b4",
        )
        metsrw.FSEntry("file[1].txt", checksumtype="MNP", checksum="dummy")
        metsrw.FSEntry("file[1].txt", checksumtype="SHA-1", checksum="dummy")
        metsrw.FSEntry("file[1].txt", checksumtype="SHA-256", checksum="dummy")
        metsrw.FSEntry("file[1].txt", checksumtype="SHA-384", checksum="dummy")
        metsrw.FSEntry("file[1].txt", checksumtype="SHA-512", checksum="dummy")
        metsrw.FSEntry("file[1].txt", checksumtype="TIGER WHIRLPOOL", checksum="dummy")
        with pytest.raises(ValueError):
            metsrw.FSEntry("file[1].txt", checksumtype="DNE", checksum="dummy")

    def test_create_checksum_and_checksumtype(self):
        with pytest.raises(ValueError):
            metsrw.FSEntry("file[1].txt", checksum="daa05c683a4913b268653f7a7e36a5b4")
        with pytest.raises(ValueError):
            metsrw.FSEntry("file[1].txt", checksumtype="MD5")

    def test_file_id_directory(self):
        """ It should have no file ID. """
        d = metsrw.FSEntry("dir", type="Directory")
        assert d.file_id() is None

    def test_file_id_no_uuid(self):
        """ It should raise an exception with no file UUID. """
        f = metsrw.FSEntry("level1.txt")
        with pytest.raises(metsrw.MetsError):
            f.file_id()

    def test_file_id_success(self):
        """ It should return a file ID. """
        file_uuid = str(uuid.uuid4())
        f = metsrw.FSEntry("level1.txt", file_uuid=file_uuid)
        assert f.file_id() == "file-" + file_uuid

    def test_group_id_no_uuid(self):
        """ It should return no group ID. """
        f = metsrw.FSEntry("level1.txt")
        assert f.group_id() is None

    def test_group_id_uuid(self):
        """ It should return a group ID. """
        file_uuid = str(uuid.uuid4())
        f = metsrw.FSEntry("level1.txt", file_uuid=file_uuid)
        assert f.group_id() == "Group-" + file_uuid

    def test_group_id_derived(self):
        """ It should return the group ID for the derived from file. """
        file_uuid = str(uuid.uuid4())
        f = metsrw.FSEntry("level1.txt", file_uuid=file_uuid)
        derived = metsrw.FSEntry(
            "level3.txt", file_uuid=str(uuid.uuid4()), derived_from=f
        )
        assert derived.group_id() == "Group-" + file_uuid
        assert derived.group_id() == f.group_id()

    def test_admids(self):
        """ It should return 0 or 1 amdSecs. """
        f = metsrw.FSEntry("file[1].txt", file_uuid=str(uuid.uuid4()))
        assert len(f.admids) == 0
        f.add_premis_object("<premis>object</premis>")
        assert len(f.admids) == 1
        f.add_premis_event("<premis>event</premis>")
        # Can only have one amdSec
        assert len(f.admids) == 1

    def test_dmdids(self):
        """ It should return a DMDID for each dmdSec. """
        f = metsrw.FSEntry("file[1].txt", file_uuid=str(uuid.uuid4()))
        assert len(f.dmdids) == 0
        f.add_dublin_core("<dc />")
        assert len(f.dmdids) == 1

    def test_add_metadata_to_fsentry(self):
        f1 = metsrw.FSEntry("file[1].txt", file_uuid=str(uuid.uuid4()))
        f1.add_dublin_core("<dc />")
        assert f1.dmdsecs
        assert len(f1.dmdsecs) == 1
        assert f1.dmdsecs[0].subsection == "dmdSec"
        assert f1.dmdsecs[0].contents.mdtype == "DC"

        # Can only have 1 amdSec, so subsequent subsections are children of
        # AMDSec
        f1.add_premis_object("<premis>object</premis>")
        assert f1.amdsecs
        assert f1.amdsecs[0].subsections
        assert f1.amdsecs[0].subsections[0].subsection == "techMD"
        assert f1.amdsecs[0].subsections[0].contents.mdtype == "PREMIS:OBJECT"

        f1.add_premis_event("<premis>event</premis>")
        assert f1.amdsecs[0].subsections[1].subsection == "digiprovMD"
        assert f1.amdsecs[0].subsections[1].contents.mdtype == "PREMIS:EVENT"

        f1.add_premis_agent("<premis>agent</premis>")
        assert f1.amdsecs[0].subsections[2].subsection == "digiprovMD"
        assert f1.amdsecs[0].subsections[2].contents.mdtype == "PREMIS:AGENT"

        f1.add_premis_rights("<premis>rights</premis>")
        assert f1.amdsecs[0].subsections[3].subsection == "rightsMD"
        assert f1.amdsecs[0].subsections[3].contents.mdtype == "PREMIS:RIGHTS"

        assert len(f1.amdsecs[0].subsections) == 4

    def test_add_child(self):
        """
        It should add a new entry to the children list.
        It should add a parent link.
        It should handle duplicates.
        """
        d = metsrw.FSEntry("dir", type="Directory")
        f = metsrw.FSEntry("file[1].txt", file_uuid=str(uuid.uuid4()))

        d.add_child(f)
        assert f in d.children
        assert len(d.children) == 1
        assert f.parent is d

        d.add_child(f)
        assert f in d.children
        assert len(d.children) == 1
        assert f.parent is d

        with pytest.raises(ValueError):
            f.add_child(d)

    def test_remove_child(self):
        """
        It should remove the child from the parent's children list.
        It should remove the parent from the child's parent link.
        """
        d = metsrw.FSEntry("dir", type="Directory")
        f1 = metsrw.FSEntry("file[1].txt", file_uuid=str(uuid.uuid4()))
        f2 = metsrw.FSEntry("file2.txt", file_uuid=str(uuid.uuid4()))
        d.add_child(f1)
        d.add_child(f2)
        assert f1 in d.children
        assert f1.parent is d
        assert len(d.children) == 2

        d.remove_child(f1)

        assert f1 not in d.children
        assert f1.parent is None
        assert len(d.children) == 1

    def test_serialize_filesec_basic(self):
        """
        It should produce a mets:file element.
        It should have an ID attribute.
        It should not have ADMIDs.
        It should have a child mets:FLocat element with the path.
        """
        f = metsrw.FSEntry(
            "file[1].txt",
            file_uuid=str(uuid.uuid4()),
            checksumtype="MD5",
            checksum="daa05c683a4913b268653f7a7e36a5b4",
        )
        el = f.serialize_filesec()
        assert el.tag == "{http://www.loc.gov/METS/}file"
        assert el.attrib["ID"].startswith("file-")
        assert el.attrib["CHECKSUM"] == "daa05c683a4913b268653f7a7e36a5b4"
        assert el.attrib["CHECKSUMTYPE"] == "MD5"
        assert el.attrib.get("ADMID") is None
        assert len(el) == 1
        assert el[0].tag == "{http://www.loc.gov/METS/}FLocat"
        assert el[0].attrib["LOCTYPE"] == "OTHER"
        assert el[0].attrib["OTHERLOCTYPE"] == "SYSTEM"
        assert el[0].attrib["{http://www.w3.org/1999/xlink}href"] == "file%5B1%5D.txt"

    def test_serialize_filesec_metadata(self):
        """
        It should produce a mets:file element.
        It should have an ID attribute.
        It should have one ADMID.
        It should have a child mets:FLocat element with the path.
        """
        f = metsrw.FSEntry("file[1].txt", file_uuid=str(uuid.uuid4()))
        f.add_premis_object("<premis>object</premis>")
        el = f.serialize_filesec()
        assert el.tag == "{http://www.loc.gov/METS/}file"
        assert el.attrib["ID"].startswith("file-")
        assert len(el.attrib["ADMID"].split()) == 1
        assert len(el) == 1
        assert el[0].tag == "{http://www.loc.gov/METS/}FLocat"
        assert el[0].attrib["LOCTYPE"] == "OTHER"
        assert el[0].attrib["OTHERLOCTYPE"] == "SYSTEM"
        assert el[0].attrib["{http://www.w3.org/1999/xlink}href"] == "file%5B1%5D.txt"

    def test_serialize_filesec_not_item(self):
        """
        It should not produce a mets:file element.
        """
        f = metsrw.FSEntry("file[1].txt", type="Directory", file_uuid=str(uuid.uuid4()))
        el = f.serialize_filesec()
        assert el is None

    def test_serialize_filesec_no_use(self):
        """
        It should not produce a mets:file element.
        """
        f = metsrw.FSEntry("file[1].txt", use=None, file_uuid=str(uuid.uuid4()))
        el = f.serialize_filesec()
        assert el is None

    def test_serialize_filesec_no_path(self):
        """
        It should produce a mets:file element.
        It should not have a child mets:FLocat.
        """
        file_uuid = str(uuid.uuid4())
        f = metsrw.FSEntry(file_uuid=file_uuid, use="deletion")
        el = f.serialize_filesec()
        assert el.tag == "{http://www.loc.gov/METS/}file"
        assert el.attrib["ID"] == "file-" + file_uuid
        assert el.attrib["GROUPID"] == "Group-" + file_uuid
        assert len(el.attrib) == 2
        assert len(el) == 0

    def test_serialize_structmap_file(self):
        """
        It should produce a mets:div element.
        It should have a TYPE and LABEL.
        It should have a child mets:fptr element with FILEID.
        """
        f = metsrw.FSEntry("file[1].txt", file_uuid=str(uuid.uuid4()))
        f.add_dublin_core("<dc />")
        el = f.serialize_structmap(recurse=False)
        assert el.tag == "{http://www.loc.gov/METS/}div"
        assert el.attrib["TYPE"] == "Item"
        assert el.attrib["LABEL"] == "file[1].txt"
        assert len(el.attrib["DMDID"].split()) == 1
        assert len(el) == 1
        assert el[0].tag == "{http://www.loc.gov/METS/}fptr"
        assert el[0].attrib["FILEID"].startswith("file-")

    def test_serialize_structmap_no_recurse(self):
        """
        It should produce a mets:div element.
        It should have a TYPE and LABEL.
        It should not have children.
        """
        d = metsrw.FSEntry("dir", type="Directory")
        f = metsrw.FSEntry("file[1].txt", file_uuid=str(uuid.uuid4()))
        d.add_child(f)
        el = d.serialize_structmap(recurse=False)
        assert el.tag == "{http://www.loc.gov/METS/}div"
        assert el.attrib["TYPE"] == "Directory"
        assert el.attrib["LABEL"] == "dir"
        assert len(el) == 0

    def test_serialize_structmap_recurse(self):
        """
        It should produce a mets:div element.
        It should have a TYPE and LABEL.
        It should have a child mets:div with the file.
        """
        d = metsrw.FSEntry("dir", type="Directory")
        f = metsrw.FSEntry("file[1].txt", file_uuid=str(uuid.uuid4()))
        d.add_child(f)
        el = d.serialize_structmap(recurse=True)
        assert el.tag == "{http://www.loc.gov/METS/}div"
        assert el.attrib["TYPE"] == "Directory"
        assert el.attrib["LABEL"] == "dir"
        assert len(el) == 1
        assert el[0].tag == "{http://www.loc.gov/METS/}div"
        assert el[0].attrib["TYPE"] == "Item"
        assert el[0].attrib["LABEL"] == "file[1].txt"
        assert len(el[0]) == 1
        assert el[0][0].tag == "{http://www.loc.gov/METS/}fptr"
        assert el[0][0].attrib["FILEID"].startswith("file-")

    def test_serialize_structmap_no_label(self):
        """ It should return None. """
        f = metsrw.FSEntry()
        el = f.serialize_structmap(recurse=False)
        assert el is None

    def test_serialize_structmap_child_empty(self):
        """ It should handle children with no structMap entry. """
        d = metsrw.FSEntry("dir", type="Directory")
        f = metsrw.FSEntry(use="deletion", file_uuid=str(uuid.uuid4()))
        d.add_child(f)
        el = d.serialize_structmap(recurse=True)
        assert el.tag == "{http://www.loc.gov/METS/}div"
        assert el.attrib["TYPE"] == "Directory"
        assert el.attrib["LABEL"] == "dir"
        assert len(el.attrib) == 2
        assert len(el) == 0

    def test_is_empty_dir(self):
        """It should be able to determine whether it is an empty directory."""

        r = metsrw.FSEntry("dir", type="Directory")
        d1 = metsrw.FSEntry("dir", type="Directory")
        d2 = metsrw.FSEntry("dir", type="Directory")
        d1a = metsrw.FSEntry("dir", type="Directory")
        d2a = metsrw.FSEntry("dir", type="Directory")
        d2b = metsrw.FSEntry("dir", type="Directory")
        f = metsrw.FSEntry("file[1].txt", file_uuid=str(uuid.uuid4()))
        r.add_child(d1)
        r.add_child(d2)
        d1.add_child(d1a)
        d2.add_child(d2a)
        d2.add_child(d2b)
        d1a.add_child(f)

        assert d2a.is_empty_dir
        assert not d2a.children
        assert not d1a.is_empty_dir
        assert len(d1a.children) == 1
        assert not d1.is_empty_dir
        assert not r.is_empty_dir
        assert not f.is_empty_dir
        # Directory d2 is an empty directory because it contains nothing but
        # empty directories.
        assert d2.is_empty_dir
        assert len(d2.children) == 2
