from lxml import etree
import pytest
from unittest import TestCase

import metsrw


class TestAMDSec(TestCase):
    """ Test AMDSec class. """

    def test_identifier(self):
        # should be in the format 'amdSec_1'
        amdsec = metsrw.AMDSec()
        assert amdsec.id_string()


class TestSubSection(TestCase):
    """ Test SubSection class. """

    STUB_MDWRAP = metsrw.MDWrap('<foo/>', 'PREMIS:DUMMY')

    def test_allowed_tags(self):
        """ It should only allow certain subsection tags. """
        with pytest.raises(ValueError):
            metsrw.SubSection('fakeMD', None)
        metsrw.SubSection('dmdSec', None)
        metsrw.SubSection('techMD', None)
        metsrw.SubSection('rightsMD', None)
        metsrw.SubSection('sourceMD', None)
        metsrw.SubSection('digiprovMD', None)

    def test_replace_with_diff_type(self):
        """ It should assert if replacing with a different subsection type. """
        dmdsec = metsrw.SubSection('dmdSec', self.STUB_MDWRAP)
        rightsmd = metsrw.SubSection('rightsMD', self.STUB_MDWRAP)
        with pytest.raises(metsrw.MetsError):
            dmdsec.replace_with(rightsmd)

    def test_replacement_techmd(self):
        """ It should have no special behaviour replacing techMDs. """
        techmd_old = metsrw.SubSection('techMD', self.STUB_MDWRAP)
        techmd_new = metsrw.SubSection('techMD', self.STUB_MDWRAP)
        techmd_old.replace_with(techmd_new)
        assert techmd_old.get_status() is None
        assert techmd_new.get_status() is None

    def test_replacement_sourcemd(self):
        """ It should have no special behaviour replacing sourceMDs. """
        sourcemd_old = metsrw.SubSection('sourceMD', self.STUB_MDWRAP)
        sourcemd_new = metsrw.SubSection('sourceMD', self.STUB_MDWRAP)
        sourcemd_old.replace_with(sourcemd_new)
        assert sourcemd_old.get_status() is None
        assert sourcemd_new.get_status() is None

    def test_replacement_digiprovmd(self):
        """ It should have no special behaviour replacing digiprovMDs. """
        digiprovmd_old = metsrw.SubSection('digiprovMD', self.STUB_MDWRAP)
        digiprovmd_new = metsrw.SubSection('digiprovMD', self.STUB_MDWRAP)
        digiprovmd_old.replace_with(digiprovmd_new)
        assert digiprovmd_old.get_status() is None
        assert digiprovmd_new.get_status() is None

    def test_replacement_rightsmd(self):
        """
        It should mark the most recent rightsMD 'current'.
        It should mark all other rightsMDs 'superseded'.
        """
        rightsmd_old = metsrw.SubSection('rightsMD', self.STUB_MDWRAP)
        assert rightsmd_old.get_status() == 'current'
        rightsmd_new = metsrw.SubSection('rightsMD', self.STUB_MDWRAP)
        rightsmd_old.replace_with(rightsmd_new)
        assert rightsmd_old.get_status() == 'superseded'
        assert rightsmd_new.get_status() == 'current'
        rightsmd_newer = metsrw.SubSection('rightsMD', self.STUB_MDWRAP)
        rightsmd_new.replace_with(rightsmd_newer)
        assert rightsmd_old.get_status() == 'superseded'
        assert rightsmd_new.get_status() == 'superseded'
        assert rightsmd_newer.get_status() == 'current'

    def test_replacement_dmdsec(self):
        """
        It should mark the first dmdSec 'original'.
        It should mark all other dmdSecs 'updated'.
        """
        dmdsec_old = metsrw.SubSection('dmdSec', self.STUB_MDWRAP)
        assert dmdsec_old.get_status() == 'original'
        dmdsec_new = metsrw.SubSection('dmdSec', self.STUB_MDWRAP)
        dmdsec_old.replace_with(dmdsec_new)
        assert dmdsec_old.get_status() == 'original'
        assert dmdsec_new.get_status() == 'updated'
        dmdsec_newer = metsrw.SubSection('dmdSec', self.STUB_MDWRAP)
        dmdsec_new.replace_with(dmdsec_newer)
        assert dmdsec_old.get_status() == 'original'
        assert dmdsec_new.get_status() == 'updated'
        assert dmdsec_newer.get_status() == 'updated'

    def test_subsection_serialize(self):
        content = metsrw.MDWrap('<foo/>', None)
        content.serialize = lambda: etree.Element('dummy_data')
        subsection = metsrw.SubSection('techMD', content)
        subsection._id = 'techMD_1'

        target = '<ns0:techMD xmlns:ns0="http://www.loc.gov/METS/" CREATED="2014-07-23T21:48:33" ID="techMD_1"><dummy_data/></ns0:techMD>'

        assert etree.tostring(subsection.serialize("2014-07-23T21:48:33")) == target

    def test_subsection_ordering(self):
        l = []
        l.append(metsrw.SubSection('digiprovMD', self.STUB_MDWRAP))
        l.append(metsrw.SubSection('sourceMD', self.STUB_MDWRAP))
        l.append(metsrw.SubSection('rightsMD', self.STUB_MDWRAP))
        l.append(metsrw.SubSection('techMD', self.STUB_MDWRAP))
        l.sort()
        assert l[0].subsection == 'techMD'
        assert l[1].subsection == 'rightsMD'
        assert l[2].subsection == 'sourceMD'
        assert l[3].subsection == 'digiprovMD'


class TestMDRef(TestCase):
    """ Test MDRef class. """

    def test_create_defaults(self):
        mdref = metsrw.MDRef('path/to/file.txt', 'PREMIS:DUMMY', 'URL')
        mdreffed = mdref.serialize()

        assert mdreffed.get('LOCTYPE') == 'URL'
        assert mdreffed.get(metsrw.lxmlns('xlink') + 'href') == 'path/to/file.txt'
        assert mdreffed.get('MDTYPE') == 'PREMIS:DUMMY'

    def test_create_extra_params(self):
        mdref = metsrw.MDRef(
            target='path/to/file.txt',
            mdtype='OTHER',
            label='Label',
            loctype='OTHER',
            otherloctype='OUTSIDE'
        )
        mdreffed = mdref.serialize()

        assert mdreffed.get('LOCTYPE') == 'OTHER'
        assert mdreffed.get('OTHERLOCTYPE') == 'OUTSIDE'
        assert mdreffed.get(metsrw.lxmlns('xlink') + 'href') == 'path/to/file.txt'
        assert mdreffed.get('MDTYPE') == 'OTHER'

    def test_create_bad_loctype(self):
        metsrw.MDRef(None, None, loctype='ARK')
        metsrw.MDRef(None, None, loctype='URN')
        metsrw.MDRef(None, None, loctype='URL')
        metsrw.MDRef(None, None, loctype='PURL')
        metsrw.MDRef(None, None, loctype='HANDLE')
        metsrw.MDRef(None, None, loctype='DOI')
        metsrw.MDRef(None, None, loctype='OTHER')
        with pytest.raises(ValueError):
            metsrw.MDRef(None, None, loctype='BAD')

    def test_parse(self):
        # Parses correctly
        good = etree.Element('{http://www.loc.gov/METS/}mdRef', MDTYPE='dummy', LOCTYPE='URL')
        good.set('{http://www.w3.org/1999/xlink}href', 'url')
        mdref = metsrw.MDRef.parse(good)
        assert mdref.target == 'url'
        assert mdref.mdtype == 'dummy'
        assert mdref.loctype == 'URL'

    def test_parse_bad_tag_name(self):
        # Wrong tag name
        bad = etree.Element('foo')
        with pytest.raises(metsrw.ParseError) as e:
            metsrw.MDRef.parse(bad)
            assert 'METS namespace' in e.value

    def test_parse_no_mdtype(self):
        # No MDTYPE
        bad = etree.Element('{http://www.loc.gov/METS/}mdRef')
        with pytest.raises(metsrw.ParseError) as e:
            metsrw.MDRef.parse(bad)
            assert 'MDTYPE' in e.value

    def test_parse_no_href(self):
        # No xlink:href
        bad = etree.Element('{http://www.loc.gov/METS/}mdRef', MDTYPE='PREMIS:DUMMY')
        with pytest.raises(metsrw.ParseError) as e:
            metsrw.MDRef.parse(bad)
            assert 'xlink:href' in e.value

    def test_parse_no_loctype(self):
        # No LOCTYPE
        bad = etree.Element('{http://www.loc.gov/METS/}mdRef', MDTYPE='PREMIS:DUMMY')
        bad.set('{http://www.w3.org/1999/xlink}href', 'url')
        with pytest.raises(metsrw.ParseError) as e:
            metsrw.MDRef.parse(bad)
            assert 'LOCTYPE' in e.value


class TestMDWrap(TestCase):
    """ Test MDWrap class. """

    def test_create_defaults(self):
        mdwrap = metsrw.MDWrap('<foo/>', 'PREMIS:DUMMY')
        mdwrapped = mdwrap.serialize()

        target = '<ns0:mdWrap xmlns:ns0="http://www.loc.gov/METS/" MDTYPE="PREMIS:DUMMY"><ns0:xmlData><foo/></ns0:xmlData></ns0:mdWrap>'

        assert mdwrapped.tag == '{http://www.loc.gov/METS/}mdWrap'
        assert mdwrap.document.tag == 'foo'
        assert etree.tostring(mdwrapped) == target

    def test_parse_bad_tag(self):
        """ It should assert if the tag name is invalid. """
        bad = etree.Element('foo')
        with pytest.raises(metsrw.ParseError):
            metsrw.MDWrap.parse(bad)

    def test_parse_no_mdtype(self):
        """ It should assert if there is no MDTYPE. """
        bad = etree.Element('{http://www.loc.gov/METS/}mdWrap')
        with pytest.raises(metsrw.ParseError):
            metsrw.MDWrap.parse(bad)

    def test_parse_no_children(self):
        """ It should assert if there are no children. """
        # mdWrap has no children
        bad = etree.Element('{http://www.loc.gov/METS/}mdWrap', MDTYPE='dummy')
        with pytest.raises(metsrw.ParseError):
            metsrw.MDWrap.parse(bad)
        # xmlData has no children
        bad = etree.Element('{http://www.loc.gov/METS/}mdWrap', MDTYPE='dummy')
        etree.SubElement(bad, '{http://www.loc.gov/METS/}xmlData')
        with pytest.raises(metsrw.ParseError):
            metsrw.MDWrap.parse(bad)

    def test_parse_success(self):
        """ It should correctly parse a valid mdWrap. """
        # Parses correctly
        good = etree.Element('{http://www.loc.gov/METS/}mdWrap', MDTYPE='dummy')
        xmldata = etree.SubElement(good, '{http://www.loc.gov/METS/}xmlData')
        document = etree.SubElement(xmldata, 'foo')
        mdwrap = metsrw.MDWrap.parse(good)
        assert mdwrap.mdtype == 'dummy'
        assert mdwrap.document == document
