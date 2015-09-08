
import filecmp
from lxml import etree
import os
import pytest
from unittest import TestCase
import uuid

import metsrw

class TestMETSWriter(TestCase):
    """ Test METSWriter class. """

    def test_fromfile(self):
        mw = metsrw.METSWriter()
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse('fixtures/complete_mets.xml', parser=parser)
        mw.fromfile('fixtures/complete_mets.xml')
        assert isinstance(mw.tree, etree._ElementTree)
        assert etree.tostring(mw.tree) == etree.tostring(root)

    def test_fromstring(self):
        mw = metsrw.METSWriter()
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse('fixtures/complete_mets.xml', parser=parser)
        with open('fixtures/complete_mets.xml') as f:
            metsstring = f.read()
        mw.fromstring(metsstring)
        assert isinstance(mw.tree, etree._ElementTree)
        assert etree.tostring(mw.tree) == etree.tostring(root)

    def test_fromtree(self):
        mw = metsrw.METSWriter()
        root = etree.parse('fixtures/complete_mets.xml')
        mw.fromtree(root)
        assert isinstance(mw.tree, etree._ElementTree)
        assert etree.tostring(mw.tree) == etree.tostring(root)

    def test_parse_tree(self):
        mw = metsrw.METSWriter()
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse('fixtures/complete_mets.xml', parser=parser)
        mw.tree = root
        mw._parse_tree()
        assert mw.createdate == '2014-07-23T21:48:33'

    def test_parse_tree_createdate_too_new(self):
        mw = metsrw.METSWriter()
        root = etree.parse('fixtures/createdate_too_new.xml')
        mw.tree = root
        with pytest.raises(metsrw.ParseError):
            mw._parse_tree()

    def test_write(self):
        mw = metsrw.METSWriter()
        # mock serialize
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse('fixtures/complete_mets.xml', parser=parser).getroot()
        mw.serialize = lambda fully_qualified: root
        mw.write('test_write.xml', pretty_print=True)
        assert filecmp.cmp('fixtures/complete_mets.xml', 'test_write.xml', shallow=False)
        os.remove('test_write.xml')

    def test_mets_root(self):
        mw = metsrw.METSWriter()
        root = mw._document_root()
        location = "http://www.loc.gov/METS/ " + \
            "http://www.loc.gov/standards/mets/version18/mets.xsd"
        assert root.tag == '{http://www.loc.gov/METS/}mets'
        assert root.attrib[metsrw.lxmlns('xsi') + 'schemaLocation'] == location
        nsmap = {
            None: "http://www.loc.gov/METS/",
            'xsi': "http://www.w3.org/2001/XMLSchema-instance",
            'xlink': "http://www.w3.org/1999/xlink",
        }
        assert root.nsmap == nsmap

    def test_mets_header(self):
        mw = metsrw.METSWriter()
        date = '2014-07-16T22:52:02.480108'
        header = mw._mets_header(date)
        assert header.tag == '{http://www.loc.gov/METS/}metsHdr'
        assert header.attrib['CREATEDATE'] == date

    def test_mets_header_lastmoddate(self):
        mw = metsrw.METSWriter()
        date = '2014-07-16T22:52:02.480108'
        new_date = '3014-07-16T22:52:02.480108'
        mw.createdate = date
        header = mw._mets_header(new_date)
        assert header.tag == '{http://www.loc.gov/METS/}metsHdr'
        assert header.attrib['CREATEDATE'] == date
        assert header.attrib['LASTMODDATE'] == new_date
        assert header.attrib['CREATEDATE'] < header.attrib['LASTMODDATE']


class TestAMDSec(TestCase):
    """ Test AMDSec class. """

    def test_mdsec_identifier(self):
        # should be in the format 'amdSec_1'
        amdsec = metsrw.AMDSec()
        assert amdsec.id_string()


class TestMDWrap(TestCase):
    """ Test MDWrap class. """

    def test_create_defaults(self):
        mdwrap = metsrw.MDWrap('<foo/>', 'PREMIS:DUMMY')
        mdwrapped = mdwrap.serialize()

        target = '<ns0:mdWrap xmlns:ns0="http://www.loc.gov/METS/" MDTYPE="PREMIS:DUMMY"><ns0:xmlData><foo/></ns0:xmlData></ns0:mdWrap>'

        assert mdwrapped.tag == '{http://www.loc.gov/METS/}mdWrap'
        assert mdwrap.document.tag == 'foo'
        assert etree.tostring(mdwrapped) == target

    def test_parse(self):
        # Wrong tag name
        bad = etree.Element('foo')
        with pytest.raises(metsrw.ParseError):
            metsrw.MDWrap.parse(bad)
        # No MDTYPE
        bad = etree.Element('{http://www.loc.gov/METS/}mdWrap')
        with pytest.raises(metsrw.ParseError):
            metsrw.MDWrap.parse(bad)
        # mdWrap has no children
        bad = etree.Element('{http://www.loc.gov/METS/}mdWrap', MDTYPE='dummy')
        with pytest.raises(metsrw.ParseError):
            metsrw.MDWrap.parse(bad)
        # xmlData has no children
        bad = etree.Element('{http://www.loc.gov/METS/}mdWrap', MDTYPE='dummy')
        etree.SubElement(bad, '{http://www.loc.gov/METS/}xmlData')
        with pytest.raises(metsrw.ParseError):
            metsrw.MDWrap.parse(bad)
        # Parses correctly
        good = etree.Element('{http://www.loc.gov/METS/}mdWrap', MDTYPE='dummy')
        xmldata = etree.SubElement(good, '{http://www.loc.gov/METS/}xmlData')
        document = etree.SubElement(xmldata, 'foo')
        mdwrap = metsrw.MDWrap.parse(good)
        assert mdwrap.mdtype == 'dummy'
        assert mdwrap.document == document


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


class TestSubSection(TestCase):
    """ Test SubSection class. """

    def test_subsection_allowed_tags(self):
        with pytest.raises(ValueError):
            metsrw.SubSection('fakeMD', None)

    def test_subsection_replace_with(self):
        mdwrap = metsrw.MDWrap('<foo/>', 'PREMIS:DUMMY')
        # Different subsections
        dmdsec = metsrw.SubSection('dmdSec', mdwrap)
        rightsmd = metsrw.SubSection('rightsMD', mdwrap)
        with pytest.raises(metsrw.MetsError):
            dmdsec.replace_with(rightsmd)
        # None for techMD
        techmd_old = metsrw.SubSection('techMD', mdwrap)
        techmd_new = metsrw.SubSection('techMD', mdwrap)
        techmd_old.replace_with(techmd_new)
        assert techmd_old.get_status() is None
        assert techmd_new.get_status() is None
        # None for sourceMD
        sourcemd_old = metsrw.SubSection('sourceMD', mdwrap)
        sourcemd_new = metsrw.SubSection('sourceMD', mdwrap)
        sourcemd_old.replace_with(sourcemd_new)
        assert sourcemd_old.get_status() is None
        assert sourcemd_new.get_status() is None
        # None for digiprovMD
        digiprovmd_old = metsrw.SubSection('digiprovMD', mdwrap)
        digiprovmd_new = metsrw.SubSection('digiprovMD', mdwrap)
        digiprovmd_old.replace_with(digiprovmd_new)
        assert digiprovmd_old.get_status() is None
        assert digiprovmd_new.get_status() is None
        # rightsMD
        rightsmd_old = metsrw.SubSection('rightsMD', mdwrap)
        assert rightsmd_old.get_status() == 'current'
        rightsmd_new = metsrw.SubSection('rightsMD', mdwrap)
        rightsmd_old.replace_with(rightsmd_new)
        assert rightsmd_old.get_status() == 'superseded'
        assert rightsmd_new.get_status() == 'current'
        rightsmd_newer = metsrw.SubSection('rightsMD', mdwrap)
        rightsmd_new.replace_with(rightsmd_newer)
        assert rightsmd_old.get_status() == 'superseded'
        assert rightsmd_new.get_status() == 'superseded'
        assert rightsmd_newer.get_status() == 'current'
        # dmdsec
        dmdsec_old = metsrw.SubSection('dmdSec', mdwrap)
        assert dmdsec_old.get_status() == 'original'
        dmdsec_new = metsrw.SubSection('dmdSec', mdwrap)
        dmdsec_old.replace_with(dmdsec_new)
        assert dmdsec_old.get_status() == 'original'
        assert dmdsec_new.get_status() == 'updated'
        dmdsec_newer = metsrw.SubSection('dmdSec', mdwrap)
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
        mdwrap = metsrw.MDWrap('<foo/>', 'PREMIS:DUMMY')
        l = []
        l.append(metsrw.SubSection('digiprovMD', mdwrap))
        l.append(metsrw.SubSection('sourceMD', mdwrap))
        l.append(metsrw.SubSection('rightsMD', mdwrap))
        l.append(metsrw.SubSection('techMD', mdwrap))
        l.sort()
        assert l[0].subsection == 'techMD'
        assert l[1].subsection == 'rightsMD'
        assert l[2].subsection == 'sourceMD'
        assert l[3].subsection == 'digiprovMD'


class TestFSEntry(TestCase):
    """ Test FSEntry class. """

    def test_file_id(self):
        d = metsrw.FSEntry('dir', type='Directory')
        assert d.file_id() is None
        f = metsrw.FSEntry('level1.txt')
        with pytest.raises(metsrw.MetsError):
            f.file_id()
        file_uuid = str(uuid.uuid4())
        f = metsrw.FSEntry('level1.txt', file_uuid=file_uuid)
        assert f.file_id() == 'file-' + file_uuid

    def test_group_id(self):
        f = metsrw.FSEntry('level1.txt')
        with pytest.raises(metsrw.MetsError):
            f.group_id()
        file_uuid = str(uuid.uuid4())
        f = metsrw.FSEntry('level1.txt', file_uuid=file_uuid)
        assert f.group_id() == 'Group-' + file_uuid
        derived = metsrw.FSEntry('level3.txt', file_uuid=str(uuid.uuid4()), derived_from=f)
        assert derived.group_id() == 'Group-' + file_uuid
        assert derived.group_id() == f.group_id()

    def test_add_metadata_to_fsentry(self):
        f1 = metsrw.FSEntry('file1.txt', file_uuid=str(uuid.uuid4()))
        f1.add_dublin_core('<dc />')
        assert f1.dmdsecs
        assert len(f1.dmdsecs) == 1
        assert f1.dmdsecs[0].subsection == 'dmdSec'
        assert f1.dmdsecs[0].contents.mdtype == 'DC'

        f1.add_premis_object('<premis>object</premis>')

        assert f1.amdsecs
        assert f1.amdsecs[0].subsections
        assert f1.amdsecs[0].subsections[0].subsection == 'techMD'
        assert f1.amdsecs[0].subsections[0].contents.mdtype == 'PREMIS:OBJECT'

        f1.add_premis_event('<premis>event</premis>')
        assert f1.amdsecs[0].subsections[1].subsection == 'digiprovMD'
        assert f1.amdsecs[0].subsections[1].contents.mdtype == 'PREMIS:EVENT'

        f1.add_premis_agent('<premis>agent</premis>')
        assert f1.amdsecs[0].subsections[2].subsection == 'digiprovMD'
        assert f1.amdsecs[0].subsections[2].contents.mdtype == 'PREMIS:AGENT'

        f1.add_premis_rights('<premis>rights</premis>')
        assert f1.amdsecs[0].subsections[3].subsection == 'rightsMD'
        assert f1.amdsecs[0].subsections[3].contents.mdtype == 'PREMIS:RIGHTS'

        assert len(f1.amdsecs[0].subsections) == 4


class TestWholeMETS(TestCase):
    """ Test integration between classes. """

    def test_files(self):
        # Test collects several children deep
        f3 = metsrw.FSEntry('level3.txt', file_uuid=str(uuid.uuid4()))
        d2 = metsrw.FSEntry('dir2', type='Directory', children=[f3])
        f2 = metsrw.FSEntry('level2.txt', file_uuid=str(uuid.uuid4()))
        d1 = metsrw.FSEntry('dir1', type='Directory', children=[d2, f2])
        f1 = metsrw.FSEntry('level1.txt', file_uuid=str(uuid.uuid4()))
        d = metsrw.FSEntry('root', type='Directory', children=[d1, f1])
        mw = metsrw.METSWriter()
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
        f4 = metsrw.FSEntry('file4.txt', file_uuid=f4_uuid)
        mw.append_file(f4)
        files = mw.all_files()
        assert len(files) == 7
        assert f4 in files

    def test_get_file(self):
        # Test collects several children deep
        f3_uuid = str(uuid.uuid4())
        f3 = metsrw.FSEntry('level3.txt', file_uuid=f3_uuid)
        d2 = metsrw.FSEntry('dir2', type='Directory', children=[f3])
        f2_uuid = str(uuid.uuid4())
        f2 = metsrw.FSEntry('level2.txt', file_uuid=f2_uuid)
        d1 = metsrw.FSEntry('dir1', type='Directory', children=[d2, f2])
        f1_uuid = str(uuid.uuid4())
        f1 = metsrw.FSEntry('level1.txt', file_uuid=f1_uuid)
        d = metsrw.FSEntry('root', type='Directory', children=[d1, f1])
        mw = metsrw.METSWriter()
        mw.append_file(d)
        assert mw.get_file(f3_uuid) == f3
        assert mw.get_file(f2_uuid) == f2
        assert mw.get_file(f1_uuid) == f1
        assert mw.get_file('something') is None
        f4_uuid = str(uuid.uuid4())
        f4 = metsrw.FSEntry('file4.txt', file_uuid=f4_uuid)
        mw.append_file(f4)
        assert mw.get_file(f4_uuid) == f4

    def test_collect_mdsec_elements(self):
        f1 = metsrw.FSEntry('file1.txt', file_uuid=str(uuid.uuid4()))
        f1.amdsecs.append(metsrw.AMDSec())
        f1.dmdsecs.append(metsrw.SubSection('dmdSec', None))
        f2 = metsrw.FSEntry('file2.txt', file_uuid=str(uuid.uuid4()))
        f2.dmdsecs.append(metsrw.SubSection('dmdSec', None))
        mw = metsrw.METSWriter()
        elements = mw._collect_mdsec_elements([f1, f2])
        # Check ordering - dmdSec before amdSec
        assert isinstance(elements, list)
        assert len(elements) == 3
        assert isinstance(elements[0], metsrw.SubSection)
        assert elements[0].subsection == 'dmdSec'
        assert isinstance(elements[1], metsrw.SubSection)
        assert elements[1].subsection == 'dmdSec'
        assert isinstance(elements[2], metsrw.AMDSec)

    def test_filesec(self):
        o = metsrw.FSEntry('objects/file1.txt', file_uuid=str(uuid.uuid4()))
        p = metsrw.FSEntry('objects/file1-preservation.txt', use='preservaton', file_uuid=str(uuid.uuid4()))
        o2 = metsrw.FSEntry('objects/file2.txt', file_uuid=str(uuid.uuid4()))
        mw = metsrw.METSWriter()
        element = mw._filesec([o, p, o2])
        assert isinstance(element, etree._Element)
        assert element.tag == '{http://www.loc.gov/METS/}fileSec'
        assert len(element) == 2  # 2 groups
        assert element[0].tag == '{http://www.loc.gov/METS/}fileGrp'
        assert element[0].get('USE') == 'original'
        assert element[1].tag == '{http://www.loc.gov/METS/}fileGrp'
        assert element[1].get('USE') == 'preservaton'
        # TODO test file & FLocat

    def test_structmap(self):
        children = [
            metsrw.FSEntry('objects/file1.txt', file_uuid=str(uuid.uuid4())),
            metsrw.FSEntry('objects/file2.txt', file_uuid=str(uuid.uuid4())),
        ]
        parent = metsrw.FSEntry('objects', type='Directory', children=children)
        writer = metsrw.METSWriter()
        writer.append_file(parent)
        sm = writer._structmap()

        parent = sm.find('{http://www.loc.gov/METS/}div')
        children = parent.getchildren()

        assert sm.tag == '{http://www.loc.gov/METS/}structMap'
        assert len(children) == 2
        assert parent.get('LABEL') == 'objects'
        assert parent.get('TYPE') == 'Directory'
        assert children[0].get('LABEL') == 'file1.txt'
        assert children[0].get('TYPE') == 'Item'
        assert children[0].find('{http://www.loc.gov/METS/}fptr') is not None
        assert children[1].get('LABEL') == 'file2.txt'
        assert children[1].get('TYPE') == 'Item'
        assert children[1].find('{http://www.loc.gov/METS/}fptr') is not None

    def test_full_mets(self):
        mw = metsrw.METSWriter()
        file1 = metsrw.FSEntry('objects/object1.ext', file_uuid=str(uuid.uuid4()))
        file2 = metsrw.FSEntry('objects/object2.ext', file_uuid=str(uuid.uuid4()))
        file1p = metsrw.FSEntry('objects/object1-preservation.ext', use='preservation', file_uuid=str(uuid.uuid4()), derived_from=file1)
        file2p = metsrw.FSEntry('objects/object2-preservation.ext', use='preservation', file_uuid=str(uuid.uuid4()), derived_from=file2)
        children = [file1, file2, file1p, file2p]
        objects = metsrw.FSEntry('objects', type='Directory', children=children)
        children = [
            metsrw.FSEntry('transfers', type='Directory', children=[]),
            metsrw.FSEntry('metadata/metadata.csv', use='metadata', file_uuid=str(uuid.uuid4())),
        ]
        metadata = metsrw.FSEntry('metadata', type='Directory', children=children)
        children = [
            metsrw.FSEntry('submissionDocumentation/METS.xml', use='submissionDocumentation', file_uuid=str(uuid.uuid4())),
        ]
        sub_doc = metsrw.FSEntry('submissionDocumentation', type='Directory', children=children)
        children = [objects, metadata, sub_doc]
        sip = metsrw.FSEntry('sipname-uuid', type='Directory', children=children)
        sip.add_dublin_core('<dublincore>sip metadata</dublincore>')
        file1.add_premis_object('<premis>object</premis>')
        file1.add_premis_event('<premis>event</premis>')
        file1.add_premis_agent('<premis>agent</premis>')
        rights = file1.add_premis_rights('<premis>rights</premis>')
        rights.replace_with(file1.add_premis_rights('<premis>newer rights</premis>'))
        dc = file1.add_dublin_core('<dublincore>metadata</dublincore>')
        dc.replace_with(file1.add_dublin_core('<dublincore>newer metadata</dublincore>'))

        mw.append_file(sip)
        mw.write('full_metsrw.xml', fully_qualified=True, pretty_print=True)

        os.remove('full_metsrw.xml')
