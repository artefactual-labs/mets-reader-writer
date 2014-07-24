
import filecmp
from lxml import etree
import os
import uuid

import pytest

import mets


def test_fromfile():
    mw = mets.METSWriter()
    root = etree.parse('fixtures/complete_mets.xml')
    mw.fromfile('fixtures/complete_mets.xml')
    assert isinstance(mw.tree, etree._ElementTree)
    assert etree.tostring(mw.tree) == etree.tostring(root)


def test_fromstring():
    mw = mets.METSWriter()
    root = etree.parse('fixtures/complete_mets.xml')
    with open('fixtures/complete_mets.xml') as f:
        metsstring = f.read()
    mw.fromstring(metsstring)
    assert isinstance(mw.tree, etree._ElementTree)
    assert etree.tostring(mw.tree) == etree.tostring(root)


def test_fromtree():
    mw = mets.METSWriter()
    root = etree.parse('fixtures/complete_mets.xml')
    mw.fromtree(root)
    assert isinstance(mw.tree, etree._ElementTree)
    assert etree.tostring(mw.tree) == etree.tostring(root)


def test_parse_tree():
    mw = mets.METSWriter()
    root = etree.parse('fixtures/complete_mets.xml')
    mw.tree = root
    mw._parse_tree()
    assert mw.createdate == '2014-07-16T23:05:27'


def test_parse_tree_createdate_too_new():
    mw = mets.METSWriter()
    root = etree.parse('fixtures/createdate_too_new.xml')
    mw.tree = root
    with pytest.raises(mets.ParseError):
        mw._parse_tree()


def test_write():
    mw = mets.METSWriter()
    # mock serialize
    root = etree.parse('fixtures/complete_mets.xml').getroot()
    mw.serialize = lambda: root
    mw.write('test_write.xml')
    assert filecmp.cmp('fixtures/complete_mets.xml', 'test_write.xml', shallow=False)
    os.remove('test_write.xml')


def test_mets_root():
    mw = mets.METSWriter()
    root = mw._document_root()
    location = "http://www.loc.gov/METS/ " + \
        "http://www.loc.gov/standards/mets/version18/mets.xsd"
    assert root.tag == 'mets'
    assert root.attrib[mets.lxmlns('xsi')+'schemaLocation'] == location
    assert root.nsmap[None] == 'http://www.loc.gov/METS/'


def test_mets_header():
    mw = mets.METSWriter()
    header = mw._mets_header()
    assert header.tag == 'metsHdr'
    assert header.attrib['CREATEDATE']


def test_mets_header_lastmoddate():
    mw = mets.METSWriter()
    date = '2014-07-16T22:52:02.480108'
    mw.createdate = date
    header = mw._mets_header()
    assert header.tag == 'metsHdr'
    assert header.attrib['CREATEDATE'] == date
    assert header.attrib['LASTMODDATE']
    assert header.attrib['CREATEDATE'] < header.attrib['LASTMODDATE']


def test_mdsec_identifier():
    # should be in the format 'amdSec_1'
    amdsec = mets.AMDSec()
    assert amdsec.id_string()


def test_mdwrap():
    mdwrap = mets.MDWrap('<foo/>', 'PREMIS:DUMMY')
    mdwrapped = mdwrap.serialize()

    target = '<mdWrap MDTYPE="PREMIS:DUMMY"><xmlData><foo/></xmlData></mdWrap>'

    assert mdwrapped.tag == 'mdWrap'
    assert mdwrap.document.tag == 'foo'
    assert etree.tostring(mdwrapped) == target


def test_mdref():
    mdref = mets.MDRef('path/to/file.txt', 'PREMIS:DUMMY')
    mdreffed = mdref.serialize()

    assert mdreffed.get('LOCTYPE') == 'URL'
    assert mdreffed.get('OTHERLOCTYPE') == 'SYSTEM'
    assert mdreffed.get(mets.lxmlns('xlink')+'href') == \
        'path/to/file.txt'
    assert mdreffed.get('MDTYPE') == 'PREMIS:DUMMY'


def test_subsection_allowed_tags():
    with pytest.raises(ValueError):
        mets.SubSection('fakeMD', None)


def test_subsection_serialize():
    content = mets.MDWrap('<foo/>', None)
    content.serialize = lambda: etree.Element('dummy_data')
    subsection = mets.SubSection('techMD', content)
    subsection._id = 'techMD_1'

    target = """<techMD ID="techMD_1"><dummy_data/></techMD>"""

    assert etree.tostring(subsection.serialize()) == target


def test_subsection_ordering():
    mdwrap = mets.MDWrap('<foo/>', 'PREMIS:DUMMY')
    l = []
    l.append(mets.SubSection('digiprovMD', mdwrap))
    l.append(mets.SubSection('sourceMD', mdwrap))
    l.append(mets.SubSection('rightsMD', mdwrap))
    l.append(mets.SubSection('techMD', mdwrap))
    l.sort()
    assert l[0].subsection == 'techMD'
    assert l[1].subsection == 'rightsMD'
    assert l[2].subsection == 'sourceMD'
    assert l[3].subsection == 'digiprovMD'


def test_collect_files():
    # Test collects several children deep
    f3 = mets.FSEntry('level3.txt', file_id='file-'+str(uuid.uuid4()))
    d2 = mets.FSEntry('dir2', type='Directory', children=[f3])
    f2 = mets.FSEntry('level2.txt', file_id='file-'+str(uuid.uuid4()))
    d1 = mets.FSEntry('dir1', type='Directory', children=[d2, f2])
    f1 = mets.FSEntry('level1.txt', file_id='file-'+str(uuid.uuid4()))
    d = mets.FSEntry('root', type='Directory', children=[d1, f1])
    mw = mets.METSWriter()
    mw.append_file(d)
    files = mw._collect_files()
    assert files
    assert len(files) == 6
    assert d in files
    assert f1 in files
    assert d1 in files
    assert f2 in files
    assert d2 in files
    assert f3 in files


def collect_mdsec_elements():
    f1 = mets.FSEntry('file1.txt', file_id='file-'+str(uuid.uuid4()))
    f1.amdsec.append(mets.AMDSec())
    f1.dmdsecs.append(mets.DMDSec())
    f2 = mets.FSEntry('file2.txt', file_id='file-'+str(uuid.uuid4()))
    f2.dmdsecs.append(mets.DMDSec())
    mw = mets.METSWriter()
    elements = mw._collect_mdsec_elements([f1, f2])
    # Check ordering - dmdSec before amdSec
    assert isinstance(elements, list)
    assert len(elements) == 3
    assert isinstance(elements[0], etree._Element)
    assert elements[0].tag == 'dmdSec'
    assert isinstance(elements[1], etree._Element)
    assert elements[0].tag == 'dmdSec'
    assert isinstance(elements[2], etree._Element)
    assert elements[0].tag == 'amdSec'


def test_filesec():
    o = mets.FSEntry('objects/file1.txt', file_id='file-'+str(uuid.uuid4()))
    p = mets.FSEntry('objects/file1-preservation.txt', use='preservaton', file_id='file-'+str(uuid.uuid4()))
    o2 = mets.FSEntry('objects/file2.txt', file_id='file-'+str(uuid.uuid4()))
    mw = mets.METSWriter()
    element = mw._filesec([o,p,o2])
    assert isinstance(element, etree._Element)
    assert element.tag == 'fileSec'
    assert len(element) == 2  # 2 groups
    assert element[0].tag == 'fileGrp'
    assert element[0].get('USE') == 'original'
    assert element[1].tag == 'fileGrp'
    assert element[1].get('USE') == 'preservaton'
    # TODO test file & FLocat


def test_structmap():
    children = [
        mets.FSEntry('objects/file1.txt', file_id='file-'+str(uuid.uuid4())),
        mets.FSEntry('objects/file2.txt', file_id='file-'+str(uuid.uuid4())),
    ]
    parent = mets.FSEntry('objects', type='Directory', children=children)
    writer = mets.METSWriter()
    writer.append_file(parent)
    sm = writer._structmap()

    parent = sm.find('div')
    children = parent.getchildren()

    assert sm.tag == 'structMap'
    assert len(children) == 2
    assert parent.get('LABEL') == 'objects'
    assert parent.get('TYPE') == 'Directory'
    assert children[0].get('LABEL') == 'file1.txt'
    assert children[1].get('TYPE') == 'Item'
    assert children[1].get('LABEL') == 'file2.txt'
    assert children[1].get('TYPE') == 'Item'
    assert children[0].find('fptr') is not None


def test_full_mets():
    mw = mets.METSWriter()
    file1 = mets.FSEntry('objects/object1.ext', file_id='file-' + str(uuid.uuid4()))
    file2 = mets.FSEntry('objects/object2.ext', file_id='file-' + str(uuid.uuid4()))
    file1p = mets.FSEntry('objects/object1-preservation.ext', use='preservation', file_id='file-' + str(uuid.uuid4()))
    file2p = mets.FSEntry('objects/object2-preservation.ext', use='preservation', file_id='file-' + str(uuid.uuid4()))
    children = [file1, file2, file1p, file2p]
    objects = mets.FSEntry('objects', type='Directory', children=children)
    children = [
        mets.FSEntry('transfers', type='Directory', children=[]),
        mets.FSEntry('metadata/metadata.csv', use='metadata', file_id='file-' + str(uuid.uuid4())),
    ]
    metadata = mets.FSEntry('metadata', type='Directory', children=children)
    children = [
        mets.FSEntry('submissionDocumentation/METS.xml', use='submissionDocumentation', file_id='file-' + str(uuid.uuid4())),
    ]
    sub_doc = mets.FSEntry('submissionDocumentation', type='Directory', children=children)
    children = [objects, metadata, sub_doc]
    sip = mets.FSEntry('sipname-uuid', type='Directory', children=children)
    file1.add_premis_object('<premis>object</premis>')
    file1.add_premis_event('<premis>event</premis>')
    file1.add_premis_agent('<premis>agent</premis>')
    file1.add_premis_rights('<premis>rights</premis>')

    mw.append_file(sip)
    mw.write('full_mets.xml', pretty_print=True)

    os.remove('full_mets.xml')
