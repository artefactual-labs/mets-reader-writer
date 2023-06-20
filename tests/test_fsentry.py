import uuid
from unittest import TestCase

import pytest

import metsrw


class TestFSEntry(TestCase):
    """Test FSEntry class."""

    def test_path_is_str(self):
        """It should store the ``path`` as a str."""
        sample = "💜🎑💜"
        assert isinstance(
            metsrw.FSEntry(sample.encode("utf-8"), type="Directory").path,
            str,
        )

    def test_create_invalid_checksum_type(self):
        """It should only accept METS valid checksum types."""
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
        """It should have no file ID."""
        d = metsrw.FSEntry("dir", type="Directory")
        assert d.file_id() is None

    def test_file_id_no_uuid(self):
        """It should raise an exception with no file UUID."""
        f = metsrw.FSEntry("level1.txt")
        with pytest.raises(metsrw.MetsError):
            f.file_id()

    def test_file_id_success(self):
        """It should return a file ID."""
        file_uuid = str(uuid.uuid4())
        f = metsrw.FSEntry("level1.txt", file_uuid=file_uuid)
        assert f.file_id() == "file-" + file_uuid

    def test_aip_file_id(self):
        fsentry = metsrw.FSEntry(
            file_uuid="9b9f129c-8062-471b-a009-9ee0ad655f08",
            type="Archival Information Package",
            path="/tmp/example-1-9b9f129c-8062-471b-a009-9ee0ad655f08.7z",
        )
        assert (
            fsentry.file_id() == "file-example-1-9b9f129c-8062-471b-a009-9ee0ad655f08"
        )

    def test_group_id_no_uuid(self):
        """It should return no group ID."""
        f = metsrw.FSEntry("level1.txt")
        assert f.group_id() is None

    def test_group_id_uuid(self):
        """It should return a group ID."""
        file_uuid = str(uuid.uuid4())
        f = metsrw.FSEntry("level1.txt", file_uuid=file_uuid)
        assert f.group_id() == "Group-" + file_uuid

    def test_group_id_derived(self):
        """It should return the group ID for the derived from file."""
        file_uuid = str(uuid.uuid4())
        f = metsrw.FSEntry("level1.txt", file_uuid=file_uuid)
        derived = metsrw.FSEntry(
            "level3.txt", file_uuid=str(uuid.uuid4()), derived_from=f
        )
        assert derived.group_id() == "Group-" + file_uuid
        assert derived.group_id() == f.group_id()

    def test_admids(self):
        """It should return 0 or 1 amdSecs."""
        f = metsrw.FSEntry("file[1].txt", file_uuid=str(uuid.uuid4()))
        assert len(f.admids) == 0
        f.add_premis_object("<premis>object</premis>")
        assert len(f.admids) == 1
        f.add_premis_event("<premis>event</premis>")
        # Can only have one amdSec
        assert len(f.admids) == 1

    def test_dmdids(self):
        """It should return a DMDID for each dmdSec."""
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

    def test_dmdsec_management(self):
        """Test addition, check and deletion of dmdSecs."""
        file = metsrw.FSEntry("file[1].txt", file_uuid=str(uuid.uuid4()))
        assert file.dmdsecs == []
        assert file.dmdsecs_by_mdtype == {}
        assert file.has_dmdsec("DC") is False
        assert file.has_dmdsec("OTHER_CUSTOM") is False
        file.add_dmdsec("<dc/>", "DC")
        assert len(file.dmdsecs) == 1
        assert len(file.dmdsecs_by_mdtype["DC"]) == 1
        assert file.has_dmdsec("DC") is True
        assert file.dmdsecs[0].status == "original"
        file.add_dmdsec("<dc/>", "DC", status="update")
        assert len(file.dmdsecs) == 2
        assert len(file.dmdsecs_by_mdtype["DC"]) == 2
        assert file.dmdsecs[0].status == "original-superseded"
        assert file.dmdsecs[1].status == "update"
        assert file.dmdsecs[0].group_id == file.dmdsecs[1].group_id
        file.add_dmdsec("<dc/>", "DC", status="update")
        assert len(file.dmdsecs) == 3
        assert len(file.dmdsecs_by_mdtype["DC"]) == 3
        assert file.dmdsecs[1].status == "update-superseded"
        assert file.dmdsecs[2].status == "update"
        assert file.dmdsecs[0].group_id == file.dmdsecs[1].group_id
        assert file.dmdsecs[0].group_id == file.dmdsecs[2].group_id
        file.delete_dmdsec("DC")
        assert len(file.dmdsecs) == 3
        assert len(file.dmdsecs_by_mdtype["DC"]) == 3
        assert file.dmdsecs[2].status == "deleted"
        file.add_dmdsec("<custom/>", "OTHER", othermdtype="CUSTOM")
        assert len(file.dmdsecs) == 4
        assert len(file.dmdsecs_by_mdtype["DC"]) == 3
        assert len(file.dmdsecs_by_mdtype["OTHER_CUSTOM"]) == 1
        assert file.has_dmdsec("OTHER", othermdtype="CUSTOM") is True
        assert file.dmdsecs[3].status == "original"
        file.add_dmdsec("<custom/>", "OTHER", othermdtype="CUSTOM", status="update")
        assert len(file.dmdsecs) == 5
        assert len(file.dmdsecs_by_mdtype["DC"]) == 3
        assert len(file.dmdsecs_by_mdtype["OTHER_CUSTOM"]) == 2
        assert file.dmdsecs[3].status == "original-superseded"
        assert file.dmdsecs[4].status == "update"
        assert file.dmdsecs[3].group_id == file.dmdsecs[4].group_id
        file.add_dmdsec("<custom/>", "OTHER", othermdtype="CUSTOM", status="update")
        assert len(file.dmdsecs) == 6
        assert len(file.dmdsecs_by_mdtype["DC"]) == 3
        assert len(file.dmdsecs_by_mdtype["OTHER_CUSTOM"]) == 3
        assert file.dmdsecs[4].status == "update-superseded"
        assert file.dmdsecs[5].status == "update"
        assert file.dmdsecs[3].group_id == file.dmdsecs[4].group_id
        assert file.dmdsecs[3].group_id == file.dmdsecs[5].group_id
        file.delete_dmdsec("OTHER", othermdtype="CUSTOM")
        assert len(file.dmdsecs) == 6
        assert len(file.dmdsecs_by_mdtype["DC"]) == 3
        assert len(file.dmdsecs_by_mdtype["OTHER_CUSTOM"]) == 3
        assert file.dmdsecs[5].status == "deleted"

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

    def test_serialize_filesec_transform_files(self):
        """
        It should produce a mets:file element.
        It should have a child mets:FLocat element.
        It should have a child mets:transformFile element.
        """
        transform_files = [
            {"type": "decryption", "order": 1, "algorithm": "GPG", "key": "somekey"}
        ]
        f = metsrw.FSEntry(
            "file[1].txt", file_uuid=str(uuid.uuid4()), transform_files=transform_files
        )
        file_element = f.serialize_filesec()
        assert file_element.tag == "{http://www.loc.gov/METS/}file"
        assert file_element[0].tag == "{http://www.loc.gov/METS/}FLocat"
        assert file_element[1].tag == "{http://www.loc.gov/METS/}transformFile"
        assert file_element[1].attrib["TRANSFORMTYPE"] == "decryption"
        assert file_element[1].attrib["TRANSFORMORDER"] == "1"
        assert file_element[1].attrib["TRANSFORMALGORITHM"] == "GPG"
        assert file_element[1].attrib["TRANSFORMKEY"] == "somekey"

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
        """It should return None."""
        f = metsrw.FSEntry()
        el = f.serialize_structmap(recurse=False)
        assert el is None

    def test_serialize_structmap_child_empty(self):
        """It should handle children with no structMap entry."""
        d = metsrw.FSEntry("dir", type="Directory")
        f = metsrw.FSEntry(use="deletion", file_uuid=str(uuid.uuid4()))
        d.add_child(f)
        el = d.serialize_structmap(recurse=True)
        assert el.tag == "{http://www.loc.gov/METS/}div"
        assert el.attrib["TYPE"] == "Directory"
        assert el.attrib["LABEL"] == "dir"
        assert len(el.attrib) == 2
        assert len(el) == 0

    def test_serialize_structmap_directory_admid(self):
        """It should add the ADMID attribute to directories with amdsecs."""
        d = metsrw.FSEntry("objects", type="Directory")
        f = metsrw.FSEntry("file.txt", file_uuid=str(uuid.uuid4()))
        d.add_child(f)
        d.add_premis_object("<premis>object</premis>")
        el = d.serialize_structmap()
        assert el.attrib.get("ADMID") is not None

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

    def test_get_path(self):
        """It should be able to get or generate a relative path."""
        sip = metsrw.FSEntry(label="sip", type="Directory")
        objects = metsrw.FSEntry(label="objects", type="Directory")
        directory = metsrw.FSEntry(label="directory", type="Directory")
        file = metsrw.FSEntry("objects/directory/file.txt")
        sip.add_child(objects).add_child(directory).add_child(file)

        assert sip.get_path() is None
        assert objects.get_path() == "objects"
        assert directory.get_path() == "objects/directory"
        assert file.get_path() == "objects/directory/file.txt"

    def test_get_path_error(self):
        """It should raise AttributeError is an entry doesn't have path nor label."""
        with pytest.raises(AttributeError):
            metsrw.FSEntry().get_path()
