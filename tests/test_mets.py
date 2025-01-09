import datetime
import filecmp
import io
import os
import tempfile
import uuid
from unittest import TestCase
from unittest import mock

import pytest
from lxml import etree
from lxml.builder import ElementMaker

import metsrw


class TestMETSDocument(TestCase):
    """Test METSDocument class."""

    def test_fromfile(self):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse("fixtures/complete_mets.xml", parser=parser)
        mw = metsrw.METSDocument.fromfile("fixtures/complete_mets.xml")
        assert isinstance(mw.tree, etree._ElementTree)
        assert etree.tostring(mw.tree) == etree.tostring(root)

    def test_fromstring(self):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse("fixtures/complete_mets.xml", parser=parser)
        with open("fixtures/complete_mets.xml", "rb") as f:
            metsstring = f.read()
        mw = metsrw.METSDocument.fromstring(metsstring)
        assert isinstance(mw.tree, etree._ElementTree)
        assert etree.tostring(mw.tree) == etree.tostring(root)

    def test_fromtree(self):
        root = etree.parse("fixtures/complete_mets.xml")
        mw = metsrw.METSDocument.fromtree(root)
        assert isinstance(mw.tree, etree._ElementTree)
        assert etree.tostring(mw.tree) == etree.tostring(root)

    def test_parse(self):
        """
        It should set the correct createdate.
        It should create FSEntrys for every file and directory.
        It should associate amdSec and dmdSec with the FSEntry.
        It should associated derived files.
        """
        mw = metsrw.METSDocument()
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse("fixtures/complete_mets.xml", parser=parser)
        mw.tree = root
        mw._parse_tree()
        assert mw.createdate == "2014-07-23T21:48:33"
        assert len(mw.all_files()) == 14
        assert (
            mw.get_file(
                type="Directory", label="csv-48accdf3-e425-4874-aad3-67ade019a214"
            )
            is not None
        )
        parent = mw.get_file(type="Directory", label="objects")
        assert parent is not None
        f = mw.get_file(type="Item", label="Landing_zone.jpg")
        assert f is not None
        assert f.path == "objects/Landing_zone.jpg"
        assert f.use == "original"
        assert f.parent == parent
        assert f.children == []
        assert f.file_uuid == "ab5c67fc-8f80-4e46-9f20-8d5ae29c43f2"
        assert f.derived_from is None
        assert f.admids == ["amdSec_1"]
        assert f.dmdids == ["dmdSec_1"]
        assert f.file_id() == "file-ab5c67fc-8f80-4e46-9f20-8d5ae29c43f2"
        assert f.group_id() == "Group-ab5c67fc-8f80-4e46-9f20-8d5ae29c43f2"
        f = mw.get_file(
            type="Item", label="Landing_zone-fc33fc0e-40ef-4ad9-ba52-860368e8ce5a.tif"
        )
        assert f is not None
        assert f.path == "objects/Landing_zone-fc33fc0e-40ef-4ad9-ba52-860368e8ce5a.tif"
        assert f.use == "preservation"
        assert f.parent == parent
        assert f.children == []
        assert f.file_uuid == "e284d015-cfb0-45dd-961d-512bf0f47cf6"
        assert f.derived_from == mw.get_file(type="Item", label="Landing_zone.jpg")
        assert f.admids == ["amdSec_2"]
        assert f.dmdids == []
        assert f.file_id() == "file-e284d015-cfb0-45dd-961d-512bf0f47cf6"
        assert f.group_id() == "Group-ab5c67fc-8f80-4e46-9f20-8d5ae29c43f2"
        assert mw.get_file(type="Directory", label="metadata") is not None
        assert mw.get_file(type="Directory", label="transfers") is not None
        assert (
            mw.get_file(
                type="Directory", label="csv-55599568-90bd-46ac-b1be-d1a538793cae"
            )
            is not None
        )
        assert (
            mw.get_file(type="Directory", label="submissionDocumentation") is not None
        )
        assert (
            mw.get_file(
                type="Directory",
                label="transfer-csv-55599568-90bd-46ac-b1be-d1a538793cae",
            )
            is not None
        )

    def test_parse_dmdsecs(self):
        """It should create FSEntry's ordered dmdsecs and mapping by type."""
        mw = metsrw.METSDocument()
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse("fixtures/dmdsecs_mets.xml", parser=parser)
        mw.tree = root
        mw._parse_tree()
        objects = mw.get_file(type="Directory", label="objects")
        assert len(objects.dmdsecs) == 4
        assert objects.dmdsecs[0].id_string == "dmdSec_1"
        assert objects.dmdsecs[-1].id_string == "dmdSec_4"
        assert len(objects.dmdsecs_by_mdtype["DC"]) == 1
        assert len(objects.dmdsecs_by_mdtype["OTHER_CUSTOM"]) == 1
        assert len(objects.dmdsecs_by_mdtype["OTHER_MD_A"]) == 1
        assert len(objects.dmdsecs_by_mdtype["OTHER_MD_B"]) == 1
        file = mw.get_file(type="Item", label="Landing_zone.jpg")
        assert len(file.dmdsecs) == 5
        assert file.dmdsecs[0].id_string == "dmdSec_5"
        assert file.dmdsecs[-1].id_string == "dmdSec_9"
        assert len(file.dmdsecs_by_mdtype["DC"]) == 2
        assert len(file.dmdsecs_by_mdtype["OTHER_CUSTOM"]) == 3

    def test_parse_tree_createdate_too_new(self):
        mw = metsrw.METSDocument()
        root = etree.parse("fixtures/createdate_too_new.xml")
        mw.tree = root
        with pytest.raises(metsrw.ParseError):
            mw._parse_tree()

    def test_parse_tree_no_createdate(self):
        mw = metsrw.METSDocument()
        mets_string = b"""<?xml version='1.0' encoding='UTF-8'?>
<mets xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns="http://www.loc.gov/METS/" xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version18/mets.xsd">
  <metsHdr/><structMap TYPE="physical"></structMap>
</mets>
"""
        root = etree.fromstring(mets_string)
        mw.tree = root
        mw._parse_tree()
        assert mw.createdate is None

    def test_parse_no_groupid(self):
        """It should handle files with no GROUPID."""
        mw = metsrw.METSDocument().fromfile("fixtures/mets_without_groupid_in_file.xml")
        assert mw.get_file(file_uuid="db653873-d0ab-4bc1-9edb-2b6d2d84ab5a") is not None

    def test_write(self):
        mw = metsrw.METSDocument()
        # mock serialize
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse("fixtures/complete_mets.xml", parser=parser).getroot()
        mw.serialize = lambda fully_qualified=True: root
        mw.write("test_write.xml", pretty_print=True, encoding="ASCII")
        assert filecmp.cmp(
            "fixtures/complete_mets.xml", "test_write.xml", shallow=False
        )
        os.remove("test_write.xml")

    def test_write_encoding(self):
        """Test serialisation encodings using the ``write`` method."""
        mw = metsrw.METSDocument()
        mw.append_file(metsrw.FSEntry("path", file_uuid=str(uuid.uuid4())))
        fd, mets_path = tempfile.mkstemp()

        try:
            mw.write(mets_path)
            with open(mets_path, "rb") as file_obj:
                tree = etree.parse(file_obj)
            assert tree.docinfo.encoding == "UTF-8"
        finally:
            os.close(fd)
            os.remove(mets_path)

    def test_tostring_encoding(self):
        """Test serialisation encodings using the ``tostring`` method."""
        mw = metsrw.METSDocument()
        mw.append_file(metsrw.FSEntry("path", file_uuid=str(uuid.uuid4())))

        xml = mw.tostring()
        assert isinstance(xml, bytes)
        tree = etree.parse(io.BytesIO(xml))
        assert tree.docinfo.encoding == "UTF-8"

        xml = mw.tostring(encoding="ASCII")
        assert isinstance(xml, bytes)
        tree = etree.parse(io.BytesIO(xml))
        assert tree.docinfo.encoding == "ASCII"

        xml = mw.tostring(encoding="unicode")
        assert isinstance(xml, str)

    def test_mets_root(self):
        mw = metsrw.METSDocument()
        root = mw._document_root()
        location = (
            "http://www.loc.gov/METS/ "
            + "http://www.loc.gov/standards/mets/version1121/mets.xsd"
        )
        assert root.tag == "{http://www.loc.gov/METS/}mets"
        assert root.attrib[metsrw.lxmlns("xsi") + "schemaLocation"] == location
        nsmap = {
            "mets": "http://www.loc.gov/METS/",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xlink": "http://www.w3.org/1999/xlink",
        }
        assert root.nsmap == nsmap

    def test_mets_root_attributes(self):
        mw = metsrw.METSDocument().fromfile("fixtures/mets_without_groupid_in_file.xml")
        assert mw.objid == "44db0a40-4c76-45b9-83f1-a8adba434b43"
        assert (
            mw._document_root().attrib["OBJID"]
            == "44db0a40-4c76-45b9-83f1-a8adba434b43"
        )

    def test_mets_header(self):
        mw = metsrw.METSDocument()
        date = "2014-07-16T22:52:02.480108"
        header = mw._mets_header(date)
        assert header.tag == "{http://www.loc.gov/METS/}metsHdr"
        assert header.attrib["CREATEDATE"] == date

    def test_mets_header_lastmoddate(self):
        mw = metsrw.METSDocument()
        date = "2014-07-16T22:52:02.480108"
        new_date = "3014-07-16T22:52:02.480108"
        mw.createdate = date
        header = mw._mets_header(new_date)
        assert header.tag == "{http://www.loc.gov/METS/}metsHdr"
        assert header.attrib["CREATEDATE"] == date
        assert header.attrib["LASTMODDATE"] == new_date
        assert header.attrib["CREATEDATE"] < header.attrib["LASTMODDATE"]

    def test_mets_header_with_agent(self):
        mets = metsrw.METSDocument()
        agent = metsrw.Agent(
            role="CREATOR",
            type="SOFTWARE",
            name="39461beb-22eb-4942-88af-848cfc3462b2",
            notes=["Archivematica dashboard UUID"],
        )
        mets.agents.append(agent)

        header_element = mets._mets_header("2014-07-16T22:52:02.480108")
        agent_element = header_element.find("{http://www.loc.gov/METS/}agent")

        assert agent_element.get("ROLE") == agent.role
        assert agent_element.get("TYPE") == "OTHER"
        assert agent_element.get("OTHERTYPE") == agent.type
        assert agent_element.find("{http://www.loc.gov/METS/}name").text == agent.name
        assert (
            agent_element.find("{http://www.loc.gov/METS/}note").text == agent.notes[0]
        )

    def test_parse_header_with_agent(self):
        mets = metsrw.METSDocument.fromstring(
            b"""<?xml version='1.0' encoding='UTF-8'?>
<mets xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns="http://www.loc.gov/METS/" xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version18/mets.xsd">
    <metsHdr CREATEDATE="2015-12-16T22:38:48">
        <agent OTHERTYPE="SOFTWARE" ROLE="CREATOR" TYPE="OTHER">
            <name>39461beb-22eb-4942-88af-848cfc3462b2</name>
            <note>Archivematica dashboard UUID</note>
        </agent>
    </metsHdr>
    <structMap ID="structMap_1" LABEL="Archivematica default" TYPE="physical"/>
</mets>"""
        )

        assert len(mets.agents) == 1
        assert mets.agents[0].role == "CREATOR"
        assert mets.agents[0].type == "SOFTWARE"
        assert mets.agents[0].name == "39461beb-22eb-4942-88af-848cfc3462b2"
        assert mets.agents[0].notes[0] == "Archivematica dashboard UUID"

    def test_mets_header_with_alt_record_id(self):
        mets = metsrw.METSDocument()
        alt_record_id = metsrw.AltRecordID(
            "39461beb-22eb-4942-88af-848cfc3462b2", type="Accession ID"
        )
        mets.alternate_ids.append(alt_record_id)

        header_element = mets._mets_header("2014-07-16T22:52:02.480108")
        alt_record_id_element = header_element.find(
            "{http://www.loc.gov/METS/}altRecordID"
        )

        assert alt_record_id_element.get("TYPE") == alt_record_id.type
        assert alt_record_id_element.text == alt_record_id.text

    def test_parse_header_with_alt_record_id(self):
        mets = metsrw.METSDocument.fromstring(
            b"""<?xml version='1.0' encoding='ASCII'?>
<mets xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns="http://www.loc.gov/METS/" xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version18/mets.xsd">
    <metsHdr CREATEDATE="2015-12-16T22:38:48">
        <altRecordID TYPE="Accession Id">39461beb-22eb-4942-88af-848cfc3462b2</altRecordID>
    </metsHdr>
    <structMap ID="structMap_1" LABEL="Archivematica default" TYPE="physical"/>
</mets>"""
        )

        assert len(mets.alternate_ids) == 1
        assert mets.alternate_ids[0].type == "Accession Id"
        assert mets.alternate_ids[0].text == "39461beb-22eb-4942-88af-848cfc3462b2"

    def test_fromfile_invalid_xlink_href(self):
        """Test that ``fromfile`` raises ``ParseError`` if an xlink:href value
        in the source METS contains an unparseable URL.
        """
        with pytest.raises(metsrw.exceptions.ParseError, match="is not a valid URL."):
            metsrw.METSDocument.fromfile("fixtures/mets_invalid_xlink_hrefs.xml")

    def test_analyze_fptr(self):
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse("fixtures/mets_dir_with_fptrs.xml", parser=parser)
        mw = metsrw.METSDocument()

        # Test that exception is raised when fileSec cannot be found.
        fptr_elem = etree.fromstring('<fptr FILEID="12345"/>')
        with pytest.raises(
            metsrw.exceptions.ParseError,
            match="12345 exists in structMap but not fileSec",
        ):
            metsrw.METSDocument._analyze_fptr(fptr_elem, tree, "directory")

        # Test that exception is raised when the path cannot be decoded.
        fptr_elem = etree.fromstring(
            '<fptr FILEID="AM68.csv-fc0e52ca-a688-41c0-a10b-c1d36e21e804"/>'
        )
        with mock.patch("metsrw.utils.urldecode") as urldecode:
            urldecode.side_effect = ValueError()
            with pytest.raises(
                metsrw.exceptions.ParseError, match="is not a valid URL"
            ):
                metsrw.METSDocument._analyze_fptr(fptr_elem, tree, "directory")

        # Test the integrity of the ``FPtr`` object returned.
        fptr = mw._analyze_fptr(fptr_elem, tree, "directory")
        assert fptr == metsrw.mets.FPtr(
            fileid="AM68.csv-fc0e52ca-a688-41c0-a10b-c1d36e21e804",
            file_uuid="fc0e52ca-a688-41c0-a10b-c1d36e21e804",
            derived_from=None,
            use="original",
            path="objects/AM68.csv",
            amdids="amdSec_3",
            dmdids=None,
            checksum=None,
            checksumtype=None,
            transform_files=[],
        )

    def test_analyze_fptr_with_dmdsecs_in_filesec(self):
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse("fixtures/mets_with_dmdsecs_in_filesec.xml", parser=parser)
        fptr_elem = tree.find(
            '/mets:structMap[@TYPE="physical"]//mets:div[@LABEL="bitstream_8266.pdf"]/mets:fptr',
            namespaces=metsrw.utils.NAMESPACES,
        )

        # Test the integrity of the ``FPtr`` object returned.
        mw = metsrw.METSDocument()
        fptr = mw._analyze_fptr(fptr_elem, tree, "Item")
        assert fptr == metsrw.mets.FPtr(
            fileid="file-33f5f35a-8bde-4b94-b7cd-3d2c8b8f7a23",
            file_uuid="33f5f35a-8bde-4b94-b7cd-3d2c8b8f7a23",
            derived_from=None,
            use="original",
            path="objects/ITEM_2429-2700.zip-2023-07-07T23_05_58.201656_00_00/bitstream_8266.pdf",
            amdids="amdSec_3",
            dmdids="dmdSec_3 dmdSec_4",
            checksum=None,
            checksumtype=None,
            transform_files=[],
        )

    def test_analyze_fptr_from_aip(self):
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse("fixtures/production-pointer-file.xml", parser=parser)
        mw = metsrw.METSDocument()

        fptr_elem = tree.find("//mets:fptr[1]", namespaces=metsrw.utils.NAMESPACES)
        fptr = mw._analyze_fptr(fptr_elem, tree, "Archival Information Package")
        assert fptr.file_uuid == "7327b00f-d83a-4ae8-bb89-84fce994e827"
        assert fptr.use == "Archival Information Package"
        assert fptr.transform_files == [
            {"ALGORITHM": "bzip2", "ORDER": "1", "TYPE": "decompression"}
        ]

    def test_analyze_fptr_sets_uuid_from_aip_with_file_id_prefix(self):
        """
        Test that AIP FILEIDs with a leading `file-` are parsed properly.
        """
        tree = etree.fromstring(
            b"""<?xml version='1.0' encoding='utf-8'?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version1121/mets.xsd">
  <mets:fileSec>
    <mets:fileGrp USE="Archival Information Package">
      <mets:file ID="file-example-1-9b9f129c-8062-471b-a009-9ee0ad655f08">
        <mets:FLocat OTHERLOCTYPE="SYSTEM" LOCTYPE="OTHER" xlink:href="/tmp/example-1-9b9f129c-8062-471b-a009-9ee0ad655f08.7z"/>
      </mets:file>
    </mets:fileGrp>
  </mets:fileSec>
  <mets:structMap TYPE="physical">
    <mets:div ADMID="amdSec_1" TYPE="Archival Information Package">
      <mets:fptr FILEID="file-example-1-9b9f129c-8062-471b-a009-9ee0ad655f08"/>
    </mets:div>
  </mets:structMap>
</mets:mets>
        """
        )
        fptr_elem = tree.find(".//mets:fptr[1]", namespaces=metsrw.utils.NAMESPACES)
        fptr = metsrw.METSDocument()._analyze_fptr(
            fptr_elem, tree, "Archival Information Package"
        )

        assert fptr.file_uuid == "9b9f129c-8062-471b-a009-9ee0ad655f08"

    def test_analyze_fptr_sets_uuid_from_aic_with_file_id_prefix(self):
        """
        Test that AIC FILEIDs with a leading `file-` are parsed properly.
        """
        tree = etree.fromstring(
            b"""<?xml version='1.0' encoding='utf-8'?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version1121/mets.xsd">
  <mets:fileSec>
    <mets:fileGrp USE="Archival Information Package">
      <mets:file ID="file-aictest_replica_aic-258f73d1-08fe-4ade-9770-1d8812cde545" GROUPID="Group-258f73d1-08fe-4ade-9770-1d8812cde545" ADMID="amdSec_10">
        <mets:FLocat xlink:href="/var/archivematica/sharedDirectory/www/AIPsStore/258f/73d1/08fe/4ade/9770/1d88/12cd/e545/aictest_replica_aic-258f73d1-08fe-4ade-9770-1d8812cde545.7z" LOCTYPE="OTHER" OTHERLOCTYPE="SYSTEM"/>
        <mets:transformFile TRANSFORMTYPE="decompression" TRANSFORMORDER="1" TRANSFORMALGORITHM="bzip2"/>
      </mets:file>
    </mets:fileGrp>
  </mets:fileSec>
  <mets:structMap ID="structMap_1" LABEL="Archivematica default" TYPE="physical">
    <mets:div TYPE="Archival Information Collection" LABEL="aictest_replica_aic-258f73d1-08fe-4ade-9770-1d8812cde545.7z">
      <mets:fptr FILEID="file-aictest_replica_aic-258f73d1-08fe-4ade-9770-1d8812cde545"/>
    </mets:div>
  </mets:structMap>
  <mets:structMap ID="structMap_2" LABEL="Normative Directory Structure" TYPE="logical">
    <mets:div TYPE="Archival Information Collection" LABEL="aictest_replica_aic-258f73d1-08fe-4ade-9770-1d8812cde545.7z"/>
  </mets:structMap>
</mets:mets>
        """
        )
        fptr_elem = tree.find(".//mets:fptr[1]", namespaces=metsrw.utils.NAMESPACES)
        fptr = metsrw.METSDocument()._analyze_fptr(
            fptr_elem, tree, "Archival Information Collection"
        )

        assert fptr.file_uuid == "258f73d1-08fe-4ade-9770-1d8812cde545"

    def test_duplicate_ids(self):
        """
        We don't want duplicate ids to be generated, but if specified, they shouldn't break
        serialization.
        """
        document = metsrw.METSDocument()
        fsentry1 = metsrw.FSEntry("file[1].txt", file_uuid=str(uuid.uuid4()))
        fsentry1.add_premis_object("<premis>object</premis>")
        fsentry1.amdsecs[0].id_string = "id_1"
        fsentry2 = metsrw.FSEntry("file[2].txt", file_uuid=str(uuid.uuid4()))
        fsentry2.add_premis_object("<premis>object</premis>")
        fsentry2.amdsecs[0].id_string = "id_1"

        document.append_file(fsentry1)
        document.append_file(fsentry2)

        reloaded_document = metsrw.METSDocument.fromtree(document.serialize())
        # Third time's the charm - previously this failed
        reloaded_document = metsrw.METSDocument.fromtree(reloaded_document.serialize())
        amdsecs = reloaded_document.tree.findall("{http://www.loc.gov/METS/}amdSec")

        assert len(amdsecs) == 2
        assert amdsecs[0].get("ID") == "id_1"
        assert amdsecs[1].get("ID") == "id_1"

    def test_directory_amd_section_read(self):
        """It should populate directory AMD sections."""
        mw = metsrw.METSDocument.fromfile("fixtures/mets_directory_amd.xml")
        objects_dir = next(_ for _ in mw.all_files() if _.label == "objects")
        assert len(objects_dir.admids) == 1


class TestWholeMETS(TestCase):
    """Test integration between classes."""

    def test_files(self):
        # Test collects several children deep
        f3 = metsrw.FSEntry("level3.txt", file_uuid=str(uuid.uuid4()))
        d2 = metsrw.FSEntry("dir2", type="Directory", children=[f3])
        f2 = metsrw.FSEntry("level2.txt", file_uuid=str(uuid.uuid4()))
        d1 = metsrw.FSEntry("dir1", type="Directory", children=[d2, f2])
        f1 = metsrw.FSEntry("level1.txt", file_uuid=str(uuid.uuid4()))
        d = metsrw.FSEntry("root", type="Directory", children=[d1, f1])
        mw = metsrw.METSDocument()
        mw.append_file(d)
        files = mw.all_files()
        assert files
        assert len(files) == 6
        assert d in files
        assert f1 in files
        assert d1 in files
        assert f2 in files
        assert d2 in files
        assert f3 in files
        f4_uuid = str(uuid.uuid4())
        f4 = metsrw.FSEntry("file4.txt", file_uuid=f4_uuid)
        mw.append_file(f4)
        files = mw.all_files()
        assert len(files) == 7
        assert f4 in files

    def test_add_file_to_child(self):
        # Test collects several children deep
        f2 = metsrw.FSEntry("level2.txt", file_uuid=str(uuid.uuid4()))
        d1 = metsrw.FSEntry("dir1", type="Directory", children=[f2])
        f1 = metsrw.FSEntry("level1.txt", file_uuid=str(uuid.uuid4()))
        d = metsrw.FSEntry("root", type="Directory", children=[d1, f1])
        mw = metsrw.METSDocument()
        mw.append_file(d)
        files = mw.all_files()
        assert files
        assert len(files) == 4
        assert d in files
        assert f1 in files
        assert d1 in files
        assert f2 in files

        f3 = metsrw.FSEntry("level3.txt", file_uuid=str(uuid.uuid4()))
        d1.add_child(f3)
        files = mw.all_files()
        assert len(files) == 5
        assert f3 in files

    def test_get_file(self):
        # Setup
        f3_uuid = str(uuid.uuid4())
        f3 = metsrw.FSEntry("dir1/dir2/level3.txt", file_uuid=f3_uuid)
        d2 = metsrw.FSEntry("dir1/dir2", type="Directory", children=[f3])
        f2_uuid = str(uuid.uuid4())
        f2 = metsrw.FSEntry("dir1/level2.txt", file_uuid=f2_uuid)
        d1 = metsrw.FSEntry("dir1", type="Directory", children=[d2, f2])
        f1_uuid = str(uuid.uuid4())
        f1 = metsrw.FSEntry("level1.txt", file_uuid=f1_uuid)
        d = metsrw.FSEntry("root", type="Directory", children=[d1, f1])
        mw = metsrw.METSDocument()
        mw.append_file(d)
        # Test
        # By UUID
        assert mw.get_file(file_uuid=f3_uuid) == f3
        assert mw.get_file(file_uuid=f2_uuid) == f2
        assert mw.get_file(file_uuid=f1_uuid) == f1
        assert mw.get_file(file_uuid="does not exist") is None
        # By path
        assert mw.get_file(path="dir1/dir2/level3.txt") == f3
        assert mw.get_file(path="dir1/dir2") == d2
        assert mw.get_file(path="dir1/level2.txt") == f2
        assert mw.get_file(path="dir1") == d1
        assert mw.get_file(path="level1.txt") == f1
        assert mw.get_file(path="does not exist") is None
        # By label
        assert mw.get_file(label="level3.txt") == f3
        assert mw.get_file(label="dir2") == d2
        assert mw.get_file(label="level2.txt") == f2
        assert mw.get_file(label="dir1") == d1
        assert mw.get_file(label="level1.txt") == f1
        assert mw.get_file(label="does not exist") is None
        # By multiple
        assert mw.get_file(label="level3.txt", path="dir1/dir2/level3.txt") == f3
        assert mw.get_file(label="dir2", type="Directory") == d2
        assert mw.get_file(label="level2.txt", type="Item") == f2
        assert mw.get_file(file_uuid=None, type="Item") is None
        # Updates list
        f4_uuid = str(uuid.uuid4())
        f4 = metsrw.FSEntry("file4.txt", file_uuid=f4_uuid)
        mw.append_file(f4)
        assert mw.get_file(file_uuid=f4_uuid) == f4
        assert mw.get_file(path="file4.txt") == f4

    def test_remove_file(self):
        """It should"""
        # Setup
        f3_uuid = str(uuid.uuid4())
        f3 = metsrw.FSEntry("dir1/dir2/level3.txt", file_uuid=f3_uuid)
        d2 = metsrw.FSEntry("dir1/dir2", type="Directory", children=[f3])
        f2_uuid = str(uuid.uuid4())
        f2 = metsrw.FSEntry("dir1/level2.txt", file_uuid=f2_uuid)
        d1 = metsrw.FSEntry("dir1", type="Directory", children=[d2, f2])
        f1_uuid = str(uuid.uuid4())
        f1 = metsrw.FSEntry("level1.txt", file_uuid=f1_uuid)
        d = metsrw.FSEntry("root", type="Directory", children=[d1, f1])
        mw = metsrw.METSDocument()
        mw.append_file(d)
        assert len(mw.all_files()) == 6
        # Test remove file
        mw.remove_entry(f3)
        assert len(mw.all_files()) == 5
        assert mw.get_file(file_uuid=f3_uuid) is None
        assert f3 not in d2.children
        assert f3 not in mw.all_files()
        # Test remove dir
        mw.remove_entry(d1)
        assert len(mw.all_files()) == 2
        assert mw.get_file(path="dir1") is None
        assert d1 not in d.children
        assert d1 not in mw.all_files()
        assert f2 not in mw.all_files()
        assert d2 not in mw.all_files()
        assert f1 in d.children
        # Test remove root element
        mw.remove_entry(d)
        assert len(mw.all_files()) == 0

    def test_collect_mdsec_elements(self):
        f1 = metsrw.FSEntry("file1.txt", file_uuid=str(uuid.uuid4()))
        f1.amdsecs.append(metsrw.AMDSec())
        f1.dmdsecs.append(metsrw.SubSection("dmdSec", None))
        f2 = metsrw.FSEntry("file2.txt", file_uuid=str(uuid.uuid4()))
        f2.dmdsecs.append(metsrw.SubSection("dmdSec", None))
        mw = metsrw.METSDocument()
        elements = mw._collect_mdsec_elements([f1, f2])
        # Check ordering - dmdSec before amdSec
        assert isinstance(elements, list)
        assert len(elements) == 3
        assert isinstance(elements[0], metsrw.SubSection)
        assert elements[0].subsection == "dmdSec"
        assert isinstance(elements[1], metsrw.SubSection)
        assert elements[1].subsection == "dmdSec"
        assert isinstance(elements[2], metsrw.AMDSec)

    def test_filesec(self):
        o = metsrw.FSEntry("objects/file1.txt", file_uuid=str(uuid.uuid4()))
        p = metsrw.FSEntry(
            "objects/file1-preservation.txt",
            use="preservaton",
            file_uuid=str(uuid.uuid4()),
        )
        o2 = metsrw.FSEntry("objects/file2.txt", file_uuid=str(uuid.uuid4()))
        mw = metsrw.METSDocument()
        element = mw._filesec([o, p, o2])
        assert isinstance(element, etree._Element)
        assert element.tag == "{http://www.loc.gov/METS/}fileSec"
        assert len(element) == 2  # 2 groups
        assert element[0].tag == "{http://www.loc.gov/METS/}fileGrp"
        assert element[0].get("USE") == "original"
        assert element[1].tag == "{http://www.loc.gov/METS/}fileGrp"
        assert element[1].get("USE") == "preservaton"
        # TODO test file & FLocat

    def test_structmap(self):
        """
        It should create a structMap tag.
        It should have a div tag for the directory.
        It should have div tags for the children beneath the directory.
        It should not have div tags for deleted files (without label).
        """
        children = [
            metsrw.FSEntry("objects/file1.txt", file_uuid=str(uuid.uuid4())),
            metsrw.FSEntry("objects/file2.txt", file_uuid=str(uuid.uuid4())),
        ]
        parent = metsrw.FSEntry("objects", type="Directory", children=children)
        deleted_f = metsrw.FSEntry(use="deletion", file_uuid=str(uuid.uuid4()))

        writer = metsrw.METSDocument()
        writer.append_file(parent)
        writer.append_file(deleted_f)
        sm = writer._structmap()

        assert sm.tag == "{http://www.loc.gov/METS/}structMap"
        assert sm.attrib["TYPE"] == "physical"
        assert sm.attrib["ID"] == "structMap_1"
        assert sm.attrib["LABEL"] == "Archivematica default"
        assert len(sm.attrib) == 3
        assert len(sm) == 1
        parent = sm[0]
        assert parent.tag == "{http://www.loc.gov/METS/}div"
        assert parent.attrib["LABEL"] == "objects"
        assert parent.attrib["TYPE"] == "Directory"
        assert len(parent.attrib) == 2
        assert len(parent) == 2
        assert parent[0].attrib["LABEL"] == "file1.txt"
        assert parent[0].attrib["TYPE"] == "Item"
        assert len(parent[0].attrib) == 2
        assert parent[0].find("{http://www.loc.gov/METS/}fptr") is not None
        assert parent[1].attrib["LABEL"] == "file2.txt"
        assert parent[1].attrib["TYPE"] == "Item"
        assert len(parent[1].attrib) == 2
        assert parent[1].find("{http://www.loc.gov/METS/}fptr") is not None

    def test_full_mets(self):
        mw = metsrw.METSDocument()
        file1 = metsrw.FSEntry("objects/object1.ext", file_uuid=str(uuid.uuid4()))
        file2 = metsrw.FSEntry("objects/object2.ext", file_uuid=str(uuid.uuid4()))
        file1p = metsrw.FSEntry(
            "objects/object1-preservation.ext",
            use="preservation",
            file_uuid=str(uuid.uuid4()),
            derived_from=file1,
        )
        file2p = metsrw.FSEntry(
            "objects/object2-preservation.ext",
            use="preservation",
            file_uuid=str(uuid.uuid4()),
            derived_from=file2,
        )
        children = [file1, file2, file1p, file2p]
        objects = metsrw.FSEntry("objects", type="Directory", children=children)
        children = [
            metsrw.FSEntry("transfers", type="Directory", children=[]),
            metsrw.FSEntry(
                "metadata/metadata.csv", use="metadata", file_uuid=str(uuid.uuid4())
            ),
        ]
        metadata = metsrw.FSEntry("metadata", type="Directory", children=children)
        children = [
            metsrw.FSEntry(
                "submissionDocumentation/METS.xml",
                use="submissionDocumentation",
                file_uuid=str(uuid.uuid4()),
            )
        ]
        sub_doc = metsrw.FSEntry(
            "submissionDocumentation", type="Directory", children=children
        )
        children = [objects, metadata, sub_doc]
        sip = metsrw.FSEntry("sipname-uuid", type="Directory", children=children)
        sip.add_dublin_core("<dublincore>sip metadata</dublincore>")
        file1.add_premis_object("<premis>object</premis>")
        file1.add_premis_event("<premis>event</premis>")
        file1.add_premis_agent("<premis>agent</premis>")
        rights = file1.add_premis_rights("<premis>rights</premis>")
        rights.replace_with(file1.add_premis_rights("<premis>newer rights</premis>"))
        dc = file1.add_dublin_core("<dublincore>metadata</dublincore>")
        dc.replace_with(
            file1.add_dublin_core("<dublincore>newer metadata</dublincore>")
        )

        mw.append_file(sip)
        mw.write("full_metsrw.xml", fully_qualified=True, pretty_print=True)
        os.remove("full_metsrw.xml")

    def test_pointer_file(self):
        """Test the creation of pointer files."""

        # Mocks of the AIP, its compression event, and other details.
        aip_uuid = str(uuid.uuid4())
        aip = {
            "current_path": f"/path/to/myaip-{aip_uuid}.7z",
            "uuid": aip_uuid,
            "package_type": "Archival Information Package",
            "checksum_algorithm": "sha256",
            "checksum": "78e4509313928d2964fe877a6a82f1ba728c171eedf696e3f5b0aed61ec547f6",
            "size": "11854",
            "extension": ".7z",
            "archive_tool": "7-Zip",
            "archive_tool_version": "9.20",
            "transform_files": [
                {"algorithm": "bzip2", "order": "2", "type": "decompression"},
                {"algorithm": "gpg", "order": "1", "type": "decryption"},
            ],
        }
        compression_event = {
            "uuid": str(uuid.uuid4()),
            "detail": (
                "program=7z; version=p7zip Version 9.20"
                " (locale=en_US.UTF-8,Utf16=on,HugeFiles=on,2 CPUs)"
            ),
            "outcome": "",
            # This should be the output from 7-zip or other...
            "outcome_detail_note": "",
            "agents": [
                {
                    "name": "Archivematica",
                    "type": "software",
                    "identifier_type": "preservation system",
                    "identifier_value": "Archivematica-1.6.1",
                },
                {
                    "name": "test",
                    "type": "organization",
                    "identifier_type": "repository code",
                    "identifier_value": "test",
                },
            ],
        }
        now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        pronom_conversion = {
            ".7z": {"puid": "fmt/484", "name": "7Zip format"},
            ".bz2": {"puid": "x-fmt/268", "name": "BZIP2 Compressed Archive"},
        }

        # Create the METS using metsrw
        mw = metsrw.METSDocument()

        # TODO: metsrw will prefix "file-" to the AIP UUID when creating <mets:fptr
        # FILEID> and <mets:file ID> attr vals. However, we want "file-" to be
        # replaced by the AIP's (i.e., the transfer's) name.
        aip_fs_entry = metsrw.FSEntry(
            path=aip["current_path"],
            file_uuid=aip["uuid"],
            use=aip["package_type"],
            type=aip["package_type"],
            transform_files=aip["transform_files"],
        )

        premis_schema_location = (
            "info:lc/xmlns/premis-v2"
            " http://www.loc.gov/standards/premis/v2/premis-v2-2.xsd"
        )
        nsmap = {
            "mets": metsrw.NAMESPACES["mets"],
            "xsi": metsrw.NAMESPACES["xsi"],
            "xlink": metsrw.NAMESPACES["xlink"],
        }
        E_P = ElementMaker(
            namespace=metsrw.NAMESPACES["premis"],
            nsmap={"premis": metsrw.NAMESPACES["premis"]},
        )

        # Create the AIP's PREMIS:OBJECT using raw lxml
        aip_premis_object = E_P.object(
            E_P.objectIdentifier(
                E_P.objectIdentifierType("UUID"), E_P.objectIdentifierValue(aip["uuid"])
            ),
            E_P.objectCharacteristics(
                E_P.compositionLevel("1"),
                E_P.fixity(
                    E_P.messageDigestAlgorithm(aip["checksum_algorithm"]),
                    E_P.messageDigest(aip["checksum"]),
                ),
                E_P.size(str(aip["size"])),
                E_P.format(
                    E_P.formatDesignation(
                        E_P.formatName(pronom_conversion[aip["extension"]]["name"]),
                        E_P.formatVersion(),
                    ),
                    E_P.formatRegistry(
                        E_P.formatRegistryName("PRONOM"),
                        E_P.formatRegistryKey(
                            pronom_conversion[aip["extension"]]["puid"]
                        ),
                    ),
                ),
                E_P.creatingApplication(
                    E_P.creatingApplicationName(aip["archive_tool"]),
                    E_P.creatingApplicationVersion(aip["archive_tool_version"]),
                    E_P.dateCreatedByApplication(now),
                ),
            ),
            version="2.2",
        )
        aip_premis_object.attrib["{" + nsmap["xsi"] + "}type"] = "premis:file"
        aip_premis_object.attrib["{" + nsmap["xsi"] + "}schemaLocation"] = (
            premis_schema_location
        )
        aip_fs_entry.add_premis_object(aip_premis_object)

        # Create the AIP's PREMIS:EVENT for the compression using raw lxml
        aip_premis_compression_event = E_P.event(
            E_P.eventIdentifier(
                E_P.eventIdentifierType("UUID"),
                E_P.eventIdentifierValue(compression_event["uuid"]),
            ),
            E_P.eventType("compression"),
            E_P.eventDateTime(now),
            E_P.eventDetail(compression_event["detail"]),
            E_P.eventOutcomeInformation(
                E_P.eventOutcome(compression_event["outcome"]),
                E_P.eventOutcomeDetail(
                    E_P.eventOutcomeDetailNote(compression_event["outcome_detail_note"])
                ),
            ),
            *[
                E_P.linkingAgentIdentifier(
                    E_P.linkingAgentIdentifierType(ag["identifier_type"]),
                    E_P.linkingAgentIdentifierValue(ag["identifier_value"]),
                )
                for ag in compression_event["agents"]
            ],
            version="2.2",
        )
        aip_premis_compression_event.attrib["{" + nsmap["xsi"] + "}schemaLocation"] = (
            premis_schema_location
        )
        aip_fs_entry.add_premis_event(aip_premis_compression_event)

        # Create the AIP's PREMIS:AGENTs using raw lxml
        for agent in compression_event["agents"]:
            agent_el = E_P.agent(
                E_P.agentIdentifier(
                    E_P.agentIdentifierType(agent["identifier_type"]),
                    E_P.agentIdentifierValue(agent["identifier_value"]),
                ),
                E_P.agentName(agent["name"]),
                E_P.agentType(agent["type"]),
            )
            agent_el.attrib["{" + nsmap["xsi"] + "}schemaLocation"] = (
                premis_schema_location
            )
            aip_fs_entry.add_premis_agent(agent_el)

        mw.append_file(aip_fs_entry)
        self.assert_pointer_valid(mw.serialize())

    def test_production_mets_file(self):
        mets_path = "fixtures/production-aip-mets-file.xml"
        mets_doc = etree.parse(mets_path)
        self.assert_mets_valid(mets_doc)

    def test_production_pointer_file(self):
        mets_path = "fixtures/production-pointer-file.xml"
        mets_doc = etree.parse(mets_path)
        self.assert_pointer_valid(mets_doc)

    def test_parse_production_pointer_file(self):
        """Test that we can use ``get_file`` to get the FSEntry instance
        representing the AIP using the AIP's UUID. This is made challenging by
        the fact that in pointer files the FILEID attribute's value is NOT
        prefixed by "file-".
        """
        mets_path = "fixtures/production-pointer-file.xml"
        mw = metsrw.METSDocument.fromfile(mets_path)
        aip_uuid = "7327b00f-d83a-4ae8-bb89-84fce994e827"
        assert mw.get_file(file_uuid=aip_uuid)

    def test_parse_dir_with_fptrs(self):
        mets_path = "fixtures/mets_dir_with_fptrs.xml"
        mw = metsrw.METSDocument.fromfile(mets_path)
        assert len(mw.all_files()) == 5
        assert mw.get_file(type="Directory", label="objects")
        for item in (
            ["3a6a182a-40a0-4c2b-9752-fc7e91ac1edf", "objects/V00154.MPG"],
            ["431913ba-4379-4373-8798-cc5f2b9dd769", "objects/V00158.MPG"],
            ["fc0e52ca-a688-41c0-a10b-c1d36e21e804", "objects/AM68.csv"],
        ):
            assert mw.get_file(type="Item", file_uuid=item[0], path=item[1])

    def test_mets_file_with_rights(self):
        mets_path = "fixtures/transfer_mets.xml"
        mw = metsrw.METSDocument.fromfile(mets_path)

        fsentry = mw.get_file(type="Item", label="bird.mp3")
        assert len(mw.all_files()) == 11

        rights = fsentry.get_premis_rights()
        assert len(rights) == 2
        assert not fsentry.get_premis_rights_statement("<unknown>")

        rights_statement = fsentry.get_premis_rights_statement(
            "86f63d9a-aea4-4640-807b-f0c4fa33ae88"
        )
        assert rights_statement.rights_basis == "Other"
        assert len(rights_statement.rights_granted) == 1
        assert rights_statement.act == "Act donor"

    # Helper methods

    def assert_mets_valid(self, mets_doc, schematron=metsrw.AM_SCT_PATH):
        is_valid, report = metsrw.validate(mets_doc, schematron=schematron)
        if not is_valid:
            raise AssertionError(report["report"])

    def assert_pointer_valid(self, mets_doc):
        self.assert_mets_valid(mets_doc, schematron=metsrw.AM_PNTR_SCT_PATH)

    def test_read_method_and_sequence_behaviour(self):
        mets_path = "fixtures/complete_mets.xml"

        # .read works with string, bytes, path and file descriptor.
        mets_file = open(mets_path)
        with open(mets_path) as fi:
            mets_unicode = fi.read()
            mets_bytes = mets_unicode.encode("utf8")
        mets1 = metsrw.METSDocument.read(mets_path)
        mets2 = metsrw.METSDocument.read(mets_file)
        mets3 = metsrw.METSDocument.read(mets_unicode)
        mets4 = metsrw.METSDocument.read(mets_bytes)

        # iteration
        for fse1, fse2, fse3, fse4 in zip(mets1, mets2, mets3, mets4):
            assert fse1.path == fse2.path == fse3.path == fse4.path

        # len
        assert len(mets1) == len(mets2) == len(mets3) == len(mets4)

        # indexing
        assert mets1[1].path == mets2[1].path == mets3[1].path == mets4[1].path

        # slicing
        assert (
            [fse.path for fse in mets1[:2]]
            == [fse.path for fse in mets2[:2]]
            == [fse.path for fse in mets3[:2]]
            == [fse.path for fse in mets4[:2]]
        )

    def test_files_invalid_path(self):
        """Test that if you try to set the path of a FSEntry to something that
        urllib.urlparse cannot parse and then attempt to serialize the METS,
        then you will trigger a MetsError.
        """
        f1 = metsrw.FSEntry(
            "http://foo[bar.com/hello[1].pdf", file_uuid=str(uuid.uuid4())
        )
        mw = metsrw.METSDocument()
        mw.append_file(f1)
        with pytest.raises(
            metsrw.exceptions.SerializeError, match="is not a valid URL."
        ):
            mw.serialize()

    def test_serialize_normative_structmap(self):
        """Test METS serialization with and without a normative structmap."""
        mw = metsrw.METSDocument.fromfile("fixtures/mets_empty_dirs.xml")
        xpath = (
            'mets:structMap[@LABEL="Normative Directory Structure"][@TYPE="logical"]'
        )
        tree = mw.serialize()
        assert tree.find(xpath, namespaces=metsrw.NAMESPACES) is not None
        tree = mw.serialize(normative_structmap=False)
        assert tree.find(xpath, namespaces=metsrw.NAMESPACES) is None

    def test_dspace_mets_dmdsecs(self):
        mets_path = "fixtures/mets_with_dmdsecs_in_filesec.xml"
        mw = metsrw.METSDocument.fromfile(mets_path)
        fsentry = mw.get_file(
            type="Item",
            path="objects/ITEM_2429-2700.zip-2023-07-07T23_05_58.201656_00_00/bitstream_8266.pdf",
        )

        # The original object of a DSpace transfer should contain two dmdSecs:
        assert len(fsentry.dmdsecs) == 2

        # - The first contains Xpointers to descriptive metadata in
        #   the original mets.xml files exported from DSpace.
        xpointer_dmdsec = [
            dmdsec
            for dmdsec in fsentry.dmdsecs
            if isinstance(dmdsec.contents, metsrw.MDRef)
        ][0].serialize()
        assert xpointer_dmdsec.attrib.get("STATUS") == "original"
        assert xpointer_dmdsec.attrib.get("CREATED") == "2023-07-07T23:06:15"

        xpointer = xpointer_dmdsec.find(
            "mets:mdRef",
            namespaces=metsrw.utils.NAMESPACES,
        )
        assert xpointer is not None
        assert (
            xpointer.attrib.get("LABEL")
            == "mets.xml-Group-33f5f35a-8bde-4b94-b7cd-3d2c8b8f7a23"
        )
        assert xpointer.attrib.get("MDTYPE") == "OTHER"
        assert xpointer.attrib.get("LOCTYPE") == "OTHER"
        assert xpointer.attrib.get("OTHERLOCTYPE") == "SYSTEM"
        assert xpointer.attrib.get("XPTR") == "xpointer(id('dmdSec_366 dmdSec_367'))"

        # - The second dmdSec reflects the parent-child relationship between a
        #   DSpace object and its collection, using the handles as identifiers.
        dc_dmdsec = [
            dmdsec
            for dmdsec in fsentry.dmdsecs
            if isinstance(dmdsec.contents, metsrw.MDWrap)
        ][0].serialize()
        assert dc_dmdsec.attrib.get("STATUS") == "original"
        assert dc_dmdsec.attrib.get("CREATED") == "2023-07-07T23:06:15"

        identifier = dc_dmdsec.find(
            'mets:mdWrap[@MDTYPE="DC"]/mets:xmlData/dcterms:dublincore/dc:identifier',
            namespaces=metsrw.utils.NAMESPACES,
        )
        assert identifier is not None
        assert identifier.text == "hdl:2429/2700"

        terms = dc_dmdsec.find(
            'mets:mdWrap[@MDTYPE="DC"]/mets:xmlData/dcterms:dublincore/dcterms:isPartOf',
            namespaces=metsrw.utils.NAMESPACES,
        )
        assert terms is not None
        assert terms.text == "hdl:2429/1314"

    def test_dspace_mets_amdsec(self):
        mets_path = "fixtures/mets_with_dmdsecs_in_filesec.xml"
        mw = metsrw.METSDocument.fromfile(mets_path)
        fsentry = mw.get_file(
            type="Item",
            path="objects/ITEM_2429-2700.zip-2023-07-07T23_05_58.201656_00_00/bitstream_8266.pdf",
        )

        # The original object of a DSpace transfer should contain Xpointers
        # to rights metadata in the original mets.xml files exported from
        # DSpace.
        rights_md = [
            subsection.contents
            for subsection in fsentry.amdsecs[0].subsections
            if isinstance(subsection.contents, metsrw.MDRef)
        ][0].serialize()
        assert (
            rights_md.attrib.get("LABEL")
            == "mets.xml-988d7030-3cde-43f2-ac1f-2b8cf9d5a70b"
        )
        assert rights_md.attrib.get("MDTYPE") == "OTHER"
        assert rights_md.attrib.get("OTHERMDTYPE") == "METSRIGHTS"
        assert rights_md.attrib.get("LOCTYPE") == "OTHER"
        assert rights_md.attrib.get("OTHERLOCTYPE") == "SYSTEM"
        assert (
            rights_md.attrib.get("XPTR")
            == "xpointer(id('rightsMD_371 rightsMD_374 rightsMD_384 rightsMD_393 rightsMD_401 rightsMD_409 rightsMD_417 rightsMD_425'))"
        )

    def test_dspace_filegrp_sorting_in_filesec(self):
        mets_path = "fixtures/mets_with_dmdsecs_in_filesec.xml"
        mw = metsrw.METSDocument.fromfile(mets_path)
        filesec = mw._filesec()

        assert [filegrp.attrib["USE"] for filegrp in filesec] == [
            "original",
            "submissionDocumentation",
            "preservation",
            "license",
            "text/ocr",
        ]


@pytest.mark.parametrize(
    "mets_path, expected_counts",
    [
        (
            "fixtures/complete_mets.xml",
            {
                "dmdSec": 2,
                "amdSec": 7,
                "techMD": 7,
                "rightsMD": 0,
                "digiprovMD": 54,
                "sourceMD": 0,
            },
        ),
        (
            "fixtures/mets_all_rights.xml",
            {
                "dmdSec": 0,
                "amdSec": 2,
                "techMD": 2,
                "rightsMD": 5,
                "digiprovMD": 0,
                "sourceMD": 0,
            },
        ),
        (
            "fixtures/mets_directory_amd.xml",
            {
                "dmdSec": 1,
                "amdSec": 2,
                "techMD": 0,
                "rightsMD": 0,
                "digiprovMD": 0,
                "sourceMD": 1,
            },
        ),
    ],
)
def test_get_subsections_counts(mets_path, expected_counts):
    mw = metsrw.METSDocument().fromfile(mets_path)
    assert mw.get_subsections_counts() == expected_counts


@pytest.mark.parametrize(
    "file_group_uses,expected_uses_order",
    [
        (
            [
                "unknown2",
                "original",
                "unknown1",
                "text/ocr",
            ],
            [
                "original",
                "text/ocr",
                "unknown2",
                "unknown1",
            ],
        ),
        (
            [
                "unknown2",
                "unknown1",
                "original",
                "unknown3",
            ],
            [
                "original",
                "unknown2",
                "unknown1",
                "unknown3",
            ],
        ),
    ],
)
def test_filegrp_sorting_returns_non_default_groups(
    file_group_uses, expected_uses_order
):
    file_groups = {
        use: etree.Element(metsrw.utils.lxmlns("mets") + "fileGrp", USE=use)
        for use in file_group_uses
    }

    mw = metsrw.METSDocument()
    result = mw._sort_filegrps(file_groups)

    assert [g.attrib["USE"] for g in result] == expected_uses_order


def test_document_ignores_missing_bag_metadata_amdsec_on_the_objects_directory():
    mets_path = "fixtures/mets_with_missing_bag_metadata_amdsec.xml"

    mw = metsrw.METSDocument.fromfile(mets_path)

    objects_directory = mw.get_file(
        type="Directory", label="objects", path=None, use=None
    )
    assert not objects_directory.amdsecs
