from unittest import TestCase

import pytest
from lxml import etree

import metsrw


class TestAgent(TestCase):
    def test_parse_exception_on_wrong_tag(self):
        element = etree.Element("test")
        with pytest.raises(metsrw.ParseError):
            metsrw.Agent.parse(element)

    def test_parse_exception_on_missing_role(self):
        element = etree.Element(metsrw.Agent.AGENT_TAG)
        with pytest.raises(metsrw.ParseError):
            metsrw.Agent.parse(element)

    def test_parse_with_role_set(self):
        element = etree.Element(metsrw.Agent.AGENT_TAG, ROLE="CREATOR")
        agent = metsrw.Agent.parse(element)

        assert agent.role == element.get("ROLE")

    def test_parse_with_other_role_set(self):
        element = etree.Element(
            metsrw.Agent.AGENT_TAG, ROLE="OTHER", OTHERROLE="DEVELOPER"
        )
        agent = metsrw.Agent.parse(element)

        assert agent.role == element.get("OTHERROLE")

    def test_parse_with_type_set(self):
        element = etree.Element(
            metsrw.Agent.AGENT_TAG, ROLE="CREATOR", TYPE="INDIVIDUAL"
        )
        agent = metsrw.Agent.parse(element)

        assert agent.type == element.get("TYPE")

    def test_parse_with_other_type_set(self):
        element = etree.Element(
            metsrw.Agent.AGENT_TAG, ROLE="CREATOR", TYPE="OTHER", OTHERTYPE="SOFTWARE"
        )
        agent = metsrw.Agent.parse(element)

        assert agent.type == element.get("OTHERTYPE")

    def test_serialize(self):
        agent = metsrw.Agent(
            "CREATOR",
            id="1",
            type="INDIVIDUAL",
            name="An agent",
            notes=["A Note", "Another Note"],
        )
        element = agent.serialize()

        assert element.get("ID") == agent.id
        assert element.get("ROLE") == agent.role
        assert element.get("TYPE") == agent.type

        assert element[0].text == agent.name
        assert element[1].text == agent.notes[0]
        assert element[2].text == agent.notes[1]

    def test_serialize_with_other_role(self):
        agent = metsrw.Agent("PROGRAMMER")
        element = agent.serialize()

        assert element.get("OTHERROLE") == agent.role


class TestAltRecordId(TestCase):
    def test_parse_exception_on_wrong_tag(self):
        element = etree.Element("test")
        with pytest.raises(metsrw.ParseError):
            metsrw.AltRecordID.parse(element)

    def test_parse(self):
        element = etree.Element(
            metsrw.AltRecordID.ALT_RECORD_ID_TAG, ID="543", TYPE="Test"
        )
        element.text = "a-unique-id"
        alt_record_id = metsrw.AltRecordID.parse(element)

        assert alt_record_id.text == element.text
        assert alt_record_id.id == element.get("ID")
        assert alt_record_id.type == element.get("TYPE")

    def test_serialize(self):
        alt_record_id = metsrw.AltRecordID("12345", id="1", type="Accession Id")
        element = alt_record_id.serialize()

        assert element.get("ID") == alt_record_id.id
        assert element.get("TYPE") == alt_record_id.type

        assert element.text == alt_record_id.text


class TestAMDSec(TestCase):
    """Test AMDSec class."""

    def setUp(self):
        # Reset the id generation counter per test
        metsrw.metadata.AMDSec._id_generator.clear()

    def test_identifier(self):
        amdsec_ids = [metsrw.AMDSec().id_string for _ in range(10)]
        # Generate a SubSection in between to make sure our count
        # doesn't jump
        amdsec_ids.append(metsrw.AMDSec().id_string)

        for index, amdsec_id in enumerate(amdsec_ids, 1):
            assert amdsec_id == f"amdSec_{index}"

    def test_tree_no_id(self):
        with pytest.raises(ValueError) as excinfo:
            metsrw.AMDSec(tree=etree.Element("amdSec"))
        assert "section_id" in str(excinfo.value)

    def test_tree_overwrites_serialize(self):
        elem = etree.Element("temp")
        amdsec = metsrw.AMDSec(tree=elem, section_id="id1")
        assert amdsec.serialize() == elem

    def test_generate_id_skips_existing_id(self):
        element = etree.Element("amdSec")
        amdsec1 = metsrw.AMDSec(tree=element, section_id="amdSec_1")
        amdsec2 = metsrw.AMDSec()
        amdsec3 = metsrw.AMDSec()

        assert amdsec1.id_string != amdsec2.id_string
        assert amdsec1.id_string != amdsec3.id_string
        assert amdsec2.id_string != amdsec3.id_string

        assert metsrw.AMDSec.get_current_id_count() == 3


class TestSubSection(TestCase):
    """Test SubSection class."""

    STUB_MDWRAP = metsrw.MDWrap("<foo/>", "PREMIS:DUMMY")

    def setUp(self):
        # Reset the id generation counters per test
        for counter in metsrw.metadata.SubSection._id_generators.values():
            counter.clear()

    def test_identifier(self):
        tech_md_ids = [metsrw.SubSection("techMD", []).id_string for _ in range(10)]
        dmdsec_ids = [metsrw.SubSection("dmdSec", []).id_string for _ in range(10)]

        for index, tech_md_id in enumerate(tech_md_ids, 1):
            assert tech_md_id == f"techMD_{index}"

        for index, dmdsec_id in enumerate(dmdsec_ids, 1):
            assert dmdsec_id == f"dmdSec_{index}"

    def test_allowed_tags(self):
        """It should only allow certain subsection tags."""
        with pytest.raises(ValueError):
            metsrw.SubSection("fakeMD", None)
        metsrw.SubSection("dmdSec", None)
        metsrw.SubSection("techMD", None)
        metsrw.SubSection("rightsMD", None)
        metsrw.SubSection("sourceMD", None)
        metsrw.SubSection("digiprovMD", None)

    def test_replace_with_diff_type(self):
        """It should assert if replacing with a different subsection type."""
        dmdsec = metsrw.SubSection("dmdSec", self.STUB_MDWRAP)
        rightsmd = metsrw.SubSection("rightsMD", self.STUB_MDWRAP)
        with pytest.raises(metsrw.MetsError):
            dmdsec.replace_with(rightsmd)

    def test_replacement_techmd(self):
        """It should have no special behaviour replacing techMDs."""
        techmd_old = metsrw.SubSection("techMD", self.STUB_MDWRAP)
        techmd_new = metsrw.SubSection("techMD", self.STUB_MDWRAP)
        techmd_old.replace_with(techmd_new)
        assert techmd_old.get_status() == "superseded"
        assert techmd_new.get_status() == "current"

    def test_replacement_sourcemd(self):
        """It should have no special behaviour replacing sourceMDs."""
        sourcemd_old = metsrw.SubSection("sourceMD", self.STUB_MDWRAP)
        sourcemd_new = metsrw.SubSection("sourceMD", self.STUB_MDWRAP)
        sourcemd_old.replace_with(sourcemd_new)
        assert sourcemd_old.get_status() is None
        assert sourcemd_new.get_status() is None

    def test_replacement_digiprovmd(self):
        """It should have no special behaviour replacing digiprovMDs."""
        digiprovmd_old = metsrw.SubSection("digiprovMD", self.STUB_MDWRAP)
        digiprovmd_new = metsrw.SubSection("digiprovMD", self.STUB_MDWRAP)
        digiprovmd_old.replace_with(digiprovmd_new)
        assert digiprovmd_old.get_status() is None
        assert digiprovmd_new.get_status() is None

    def test_replacement_rightsmd(self):
        """
        It should mark the most recent rightsMD 'current'.
        It should mark all other rightsMDs 'superseded'.
        """
        rightsmd_old = metsrw.SubSection("rightsMD", self.STUB_MDWRAP)
        assert rightsmd_old.get_status() == "current"
        rightsmd_new = metsrw.SubSection("rightsMD", self.STUB_MDWRAP)
        rightsmd_old.replace_with(rightsmd_new)
        assert rightsmd_old.get_status() == "superseded"
        assert rightsmd_new.get_status() == "current"
        rightsmd_newer = metsrw.SubSection("rightsMD", self.STUB_MDWRAP)
        rightsmd_new.replace_with(rightsmd_newer)
        assert rightsmd_old.get_status() == "superseded"
        assert rightsmd_new.get_status() == "superseded"
        assert rightsmd_newer.get_status() == "current"

    def test_replacement_dmdsec(self):
        """
        It should mark the first dmdSec 'original'.
        It should mark all other dmdSecs 'updated'.
        """
        dmdsec_old = metsrw.SubSection("dmdSec", self.STUB_MDWRAP)
        assert dmdsec_old.get_status() == "original"
        dmdsec_new = metsrw.SubSection("dmdSec", self.STUB_MDWRAP)
        dmdsec_old.replace_with(dmdsec_new)
        assert dmdsec_old.get_status() == "original-superseded"
        assert dmdsec_new.get_status() == "update"
        dmdsec_newer = metsrw.SubSection("dmdSec", self.STUB_MDWRAP)
        dmdsec_new.replace_with(dmdsec_newer)
        assert dmdsec_old.get_status() == "original-superseded"
        assert dmdsec_new.get_status() == "update-superseded"
        assert dmdsec_newer.get_status() == "update"

    def test_subsection_serialize(self):
        content = metsrw.MDWrap("<foo/>", None)
        content.serialize = lambda: etree.Element("dummy_data")
        subsection = metsrw.SubSection("techMD", content)
        subsection._id = "techMD_1"

        root = subsection.serialize("2014-07-23T21:48:33")
        assert root.tag == "{http://www.loc.gov/METS/}techMD"
        assert root.attrib["ID"] == "techMD_1"
        assert root.attrib["CREATED"] == "2014-07-23T21:48:33"
        assert root.attrib["STATUS"] == "current"
        assert len(root.attrib) == 3
        assert len(root) == 1
        assert root[0].tag == "dummy_data"

    def test_subsection_serialize_no_date(self):
        content = metsrw.MDWrap("<foo/>", None)
        content.serialize = lambda: etree.Element("dummy_data")
        subsection = metsrw.SubSection("techMD", content)
        subsection._id = "techMD_1"

        root = subsection.serialize()
        assert root.tag == "{http://www.loc.gov/METS/}techMD"
        assert root.attrib["ID"] == "techMD_1"
        assert root.attrib["STATUS"] == "current"
        assert len(root.attrib) == 2
        assert len(root) == 1
        assert root[0].tag == "dummy_data"

    def test_subsection_ordering(self):
        list_ = []
        list_.append(metsrw.SubSection("digiprovMD", self.STUB_MDWRAP))
        list_.append(metsrw.SubSection("sourceMD", self.STUB_MDWRAP))
        list_.append(metsrw.SubSection("rightsMD", self.STUB_MDWRAP))
        list_.append(metsrw.SubSection("techMD", self.STUB_MDWRAP))
        list_.sort()
        assert list_[0].subsection == "techMD"
        assert list_[1].subsection == "rightsMD"
        assert list_[2].subsection == "sourceMD"
        assert list_[3].subsection == "digiprovMD"

    def test_parse(self):
        """
        It should parse SubSection ID, CREATED & STATUS.
        It should create an MDWrap or MDRef child.
        """
        # Parses correctly
        elem = etree.Element(
            "{http://www.loc.gov/METS/}techMD",
            ID="techMD_42",
            CREATED="2016-01-02T03:04:05",
            STATUS="original",
        )
        mdr = etree.SubElement(
            elem, "{http://www.loc.gov/METS/}mdRef", MDTYPE="dummy", LOCTYPE="URL"
        )
        mdr.set("{http://www.w3.org/1999/xlink}href", "url")
        obj = metsrw.SubSection.parse(elem)
        assert obj.subsection == "techMD"
        assert obj.status == "original"
        assert obj.created == "2016-01-02T03:04:05"
        assert obj.id_string == "techMD_42"
        assert obj.newer is obj.older is None
        assert isinstance(obj.contents, metsrw.MDRef)

    def test_parse_bad_subsection_type(self):
        """It should only accept valid subsection tags."""
        # Wrong tag name
        bad = etree.Element("foo")
        with pytest.raises(metsrw.ParseError) as e:
            metsrw.SubSection.parse(bad)
            assert "METS namespace" in e.value

    def test_parse_bad_child_type(self):
        """It should only accept valid child tags."""
        elem = etree.Element(
            "{http://www.loc.gov/METS/}techMD",
            ID="techMD_42",
            CREATED="2016-01-02T03:04:05",
            STATUS="original",
        )
        etree.SubElement(elem, "foo")
        with pytest.raises(metsrw.ParseError) as e:
            metsrw.SubSection.parse(elem)
            assert "must be mdWrap or mdRef" in e.value

    def test_roundtrip(self):
        """It should be able to parse and write out a subsection unchanged."""
        elem = etree.Element(
            "{http://www.loc.gov/METS/}techMD",
            ID="techMD_42",
            CREATED="2016-01-02T03:04:05",
            STATUS="original",
        )
        mdr = etree.SubElement(
            elem, "{http://www.loc.gov/METS/}mdRef", MDTYPE="dummy", LOCTYPE="URL"
        )
        mdr.set("{http://www.w3.org/1999/xlink}href", "url")
        obj = metsrw.SubSection.parse(elem)
        new = obj.serialize(now="2001-02-03T09:10")
        assert new.tag == "{http://www.loc.gov/METS/}techMD"
        assert new.attrib["ID"] == "techMD_42"
        assert new.attrib["CREATED"] == "2016-01-02T03:04:05"
        assert new.attrib["STATUS"] == "original"
        assert len(new.attrib) == 3

    def test_roundtrip_bare(self):
        """It should be able to parse and write out a subsection unchanged."""
        elem = etree.Element("{http://www.loc.gov/METS/}techMD", ID="techMD_42")
        mdr = etree.SubElement(
            elem, "{http://www.loc.gov/METS/}mdRef", MDTYPE="dummy", LOCTYPE="URL"
        )
        mdr.set("{http://www.w3.org/1999/xlink}href", "url")
        obj = metsrw.SubSection.parse(elem)
        new = obj.serialize(now="2001-02-03T09:10")
        assert new.tag == "{http://www.loc.gov/METS/}techMD"
        assert new.attrib["ID"] == "techMD_42"
        assert len(new.attrib) == 1

    def test_roundtrip_group_id(self):
        """It should be able to maintain the GROUPID attribute."""
        elem = etree.Element(
            "{http://www.loc.gov/METS/}dmdSec",
            ID="dmd_1",
            GROUPID="ab3ba63f-3e50-4477-964f-9c5ef2d33dc0",
        )
        mdr = etree.SubElement(
            elem, "{http://www.loc.gov/METS/}mdRef", MDTYPE="dummy", LOCTYPE="URL"
        )
        mdr.set("{http://www.w3.org/1999/xlink}href", "url")
        obj = metsrw.SubSection.parse(elem)
        new = obj.serialize()
        assert new.attrib["GROUPID"] == "ab3ba63f-3e50-4477-964f-9c5ef2d33dc0"

    def test_generate_id_skips_existing_id(self):
        techmd1 = metsrw.SubSection("techMD", [], section_id="techMD_1")
        techmd2 = metsrw.SubSection("techMD", [])
        techmd3 = metsrw.SubSection("techMD", [])

        assert techmd1.id_string != techmd2.id_string
        assert techmd1.id_string != techmd3.id_string
        assert techmd2.id_string != techmd3.id_string

        assert metsrw.SubSection.get_current_id_count("techMD") == 3


class TestMDRef(TestCase):
    """Test MDRef class."""

    def test_create_defaults(self):
        mdref = metsrw.MDRef("path/to/file.txt", "PREMIS:DUMMY", "URL")
        mdreffed = mdref.serialize()

        assert mdreffed.get("LOCTYPE") == "URL"
        assert mdreffed.get(metsrw.lxmlns("xlink") + "href") == "path/to/file.txt"
        assert mdreffed.get("MDTYPE") == "PREMIS:DUMMY"

    def test_create_extra_params(self):
        mdref = metsrw.MDRef(
            target="path/to/file.txt",
            mdtype="OTHER",
            label="Label",
            loctype="OTHER",
            otherloctype="OUTSIDE",
            xptr="xpointer(id('dmdSec_366 dmdSec_367'))",
            othermdtype="METSRIGHTS",
        )
        mdreffed = mdref.serialize()

        assert mdreffed.get("LOCTYPE") == "OTHER"
        assert mdreffed.get("OTHERLOCTYPE") == "OUTSIDE"
        assert mdreffed.get(metsrw.lxmlns("xlink") + "href") == "path/to/file.txt"
        assert mdreffed.get("MDTYPE") == "OTHER"
        assert mdreffed.get("XPTR") == "xpointer(id('dmdSec_366 dmdSec_367'))"
        assert mdreffed.get("OTHERMDTYPE") == "METSRIGHTS"

    def test_create_bad_loctype(self):
        metsrw.MDRef(None, None, loctype="ARK")
        metsrw.MDRef(None, None, loctype="URN")
        metsrw.MDRef(None, None, loctype="URL")
        metsrw.MDRef(None, None, loctype="PURL")
        metsrw.MDRef(None, None, loctype="HANDLE")
        metsrw.MDRef(None, None, loctype="DOI")
        metsrw.MDRef(None, None, loctype="OTHER")
        with pytest.raises(ValueError):
            metsrw.MDRef(None, None, loctype="BAD")

    def test_parse(self):
        # Parses correctly
        good = etree.Element(
            "{http://www.loc.gov/METS/}mdRef", MDTYPE="dummy", LOCTYPE="URL"
        )
        good.set("{http://www.w3.org/1999/xlink}href", "url")
        mdref = metsrw.MDRef.parse(good)
        assert mdref.target == "url"
        assert mdref.mdtype == "dummy"
        assert mdref.loctype == "URL"

    def test_parse_bad_tag_name(self):
        # Wrong tag name
        bad = etree.Element("foo")
        with pytest.raises(metsrw.ParseError) as e:
            metsrw.MDRef.parse(bad)
            assert "METS namespace" in e.value

    def test_parse_no_mdtype(self):
        # No MDTYPE
        bad = etree.Element("{http://www.loc.gov/METS/}mdRef")
        with pytest.raises(metsrw.ParseError) as e:
            metsrw.MDRef.parse(bad)
            assert "MDTYPE" in e.value

    def test_parse_no_href(self):
        # No xlink:href
        bad = etree.Element("{http://www.loc.gov/METS/}mdRef", MDTYPE="PREMIS:DUMMY")
        with pytest.raises(metsrw.ParseError) as e:
            metsrw.MDRef.parse(bad)
            assert "xlink:href" in e.value

    def test_parse_no_loctype(self):
        # No LOCTYPE
        bad = etree.Element("{http://www.loc.gov/METS/}mdRef", MDTYPE="PREMIS:DUMMY")
        bad.set("{http://www.w3.org/1999/xlink}href", "url")
        with pytest.raises(metsrw.ParseError) as e:
            metsrw.MDRef.parse(bad)
            assert "LOCTYPE" in e.value

    def test_url_encoding(self):
        """Good target values are URL-encoded when they show up in xlink:href
        attributes; bad target values raise ``MetsError``.
        """
        mdref = metsrw.MDRef("30_CFLQ_271_13-3-13_1524[1].pdf", "PREMIS:DUMMY", "URL")
        mdreffed = mdref.serialize()
        assert mdreffed.get(metsrw.lxmlns("xlink") + "href") == (
            "30_CFLQ_271_13-3-13_1524%5B1%5D.pdf"
        )
        with pytest.raises(
            metsrw.exceptions.SerializeError, match="is not a valid URL."
        ):
            mdref = metsrw.MDRef(
                "http://foo[bar.com/hello[1].pdf", "PREMIS:DUMMY", "URL"
            )
            mdref.serialize()


class TestMDWrap(TestCase):
    """Test MDWrap class."""

    def test_parse_bad_tag(self):
        """It should assert if the tag name is invalid."""
        bad = etree.Element("foo")
        with pytest.raises(metsrw.ParseError):
            metsrw.MDWrap.parse(bad)

    def test_parse_no_mdtype(self):
        """It should assert if there is no MDTYPE."""
        bad = etree.Element("{http://www.loc.gov/METS/}mdWrap")
        with pytest.raises(metsrw.ParseError):
            metsrw.MDWrap.parse(bad)

    def test_parse_no_children(self):
        """It should assert if there are no children."""
        # mdWrap has no children
        bad = etree.Element("{http://www.loc.gov/METS/}mdWrap", MDTYPE="dummy")
        with pytest.raises(metsrw.ParseError):
            metsrw.MDWrap.parse(bad)
        # xmlData has no children
        bad = etree.Element("{http://www.loc.gov/METS/}mdWrap", MDTYPE="dummy")
        etree.SubElement(bad, "{http://www.loc.gov/METS/}xmlData")
        with pytest.raises(metsrw.ParseError):
            metsrw.MDWrap.parse(bad)

    def test_parse_success(self):
        """It should correctly parse a valid mdWrap."""
        # Parses correctly
        good = etree.Element(
            "{http://www.loc.gov/METS/}mdWrap", MDTYPE="OTHER", OTHERMDTYPE="SYSTEM"
        )
        xmldata = etree.SubElement(good, "{http://www.loc.gov/METS/}xmlData")
        etree.SubElement(xmldata, "foo")
        mdwrap = metsrw.MDWrap.parse(good)
        assert mdwrap.mdtype == "OTHER"
        assert mdwrap.othermdtype == "SYSTEM"
        assert etree.tostring(mdwrap.document) == etree.tostring(etree.Element("foo"))

    def test_serialize_defaults(self):
        mdwrap = metsrw.MDWrap("<foo/>", "PREMIS:DUMMY")
        elem = mdwrap.serialize()

        assert elem.tag == "{http://www.loc.gov/METS/}mdWrap"
        assert elem.attrib["MDTYPE"] == "PREMIS:DUMMY"
        assert len(elem.attrib) == 1
        assert elem[0].tag == "{http://www.loc.gov/METS/}xmlData"
        assert len(elem[0].attrib) == 0
        assert elem[0][0].tag == "foo"

    def test_serialize_params(self):
        mdwrap = metsrw.MDWrap(
            etree.Element("foo"), mdtype="OTHER", othermdtype="SYSTEM"
        )
        elem = mdwrap.serialize()

        assert elem.tag == "{http://www.loc.gov/METS/}mdWrap"
        assert elem.attrib["MDTYPE"] == "OTHER"
        assert elem.attrib["OTHERMDTYPE"] == "SYSTEM"
        assert len(elem.attrib) == 2
        assert elem[0].tag == "{http://www.loc.gov/METS/}xmlData"
        assert len(elem[0].attrib) == 0
        assert elem[0][0].tag == "foo"

    def test_roundtrip(self):
        elem = etree.Element(
            "{http://www.loc.gov/METS/}mdWrap", MDTYPE="OTHER", OTHERMDTYPE="SYSTEM"
        )
        xmldata = etree.SubElement(elem, "{http://www.loc.gov/METS/}xmlData")
        etree.SubElement(xmldata, "foo")

        mdwrap = metsrw.MDWrap.parse(elem)
        elem = mdwrap.serialize()

        assert elem.tag == "{http://www.loc.gov/METS/}mdWrap"
        assert elem.attrib["MDTYPE"] == "OTHER"
        assert elem.attrib["OTHERMDTYPE"] == "SYSTEM"
        assert len(elem.attrib) == 2
        assert elem[0].tag == "{http://www.loc.gov/METS/}xmlData"
        assert len(elem[0].attrib) == 0
        assert elem[0][0].tag == "foo"

    def test_url_decoding(self):
        good = etree.Element(
            "{http://www.loc.gov/METS/}mdRef", MDTYPE="dummy", LOCTYPE="URL"
        )
        good.set(
            "{http://www.w3.org/1999/xlink}href", "30_CFLQ_271_13-3-13_1524%5B1%5D.pdf"
        )
        mdref = metsrw.MDRef.parse(good)
        assert mdref.target == "30_CFLQ_271_13-3-13_1524[1].pdf"
        with pytest.raises(metsrw.exceptions.ParseError, match="is not a valid URL"):
            bad = etree.Element(
                "{http://www.loc.gov/METS/}mdRef", MDTYPE="dummy", LOCTYPE="URL"
            )
            bad.set(
                "{http://www.w3.org/1999/xlink}href", "http://foo[bar.com/hello[1].pdf"
            )
            metsrw.MDRef.parse(bad)
