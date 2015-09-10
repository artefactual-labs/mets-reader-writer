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
        with open('fixtures/complete_mets.xml', 'rb') as f:
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
