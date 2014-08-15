
import filecmp
from lxml import etree
import os
import uuid

import pytest

import mets


def test_fromfile():
    mw = mets.METSWriter()
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse('fixtures/complete_mets.xml', parser=parser)
    mw.fromfile('fixtures/complete_mets.xml')
    assert isinstance(mw.tree, etree._ElementTree)
    assert etree.tostring(mw.tree) == etree.tostring(root)


def test_fromstring():
    mw = mets.METSWriter()
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse('fixtures/complete_mets.xml', parser=parser)
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
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse('fixtures/complete_mets.xml', parser=parser)
    mw.tree = root
    mw._parse_tree()
    assert mw.createdate == '2014-07-23T21:48:33'


def test_parse_tree_createdate_too_new():
    mw = mets.METSWriter()
    root = etree.parse('fixtures/createdate_too_new.xml')
    mw.tree = root
    with pytest.raises(mets.ParseError):
        mw._parse_tree()


def test_write():
    mw = mets.METSWriter()
    # mock serialize
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse('fixtures/complete_mets.xml', parser=parser).getroot()
    mw.serialize = lambda fully_qualified: root
    mw.write('test_write.xml', pretty_print=True)
    assert filecmp.cmp('fixtures/complete_mets.xml', 'test_write.xml', shallow=False)
    os.remove('test_write.xml')


def test_mets_root():
    mw = mets.METSWriter()
    root = mw._document_root()
    location = "http://www.loc.gov/METS/ " + \
        "http://www.loc.gov/standards/mets/version18/mets.xsd"
    assert root.tag == '{http://www.loc.gov/METS/}mets'
    assert root.attrib[mets.lxmlns('xsi')+'schemaLocation'] == location
    nsmap = {
        None: "http://www.loc.gov/METS/",
        'xsi': "http://www.w3.org/2001/XMLSchema-instance",
        'xlink': "http://www.w3.org/1999/xlink",
    }
    assert root.nsmap == nsmap


def test_mets_header():
    mw = mets.METSWriter()
    date = '2014-07-16T22:52:02.480108'
    header = mw._mets_header(date)
    assert header.tag == '{http://www.loc.gov/METS/}metsHdr'
    assert header.attrib['CREATEDATE'] == date


def test_mets_header_lastmoddate():
    mw = mets.METSWriter()
    date = '2014-07-16T22:52:02.480108'
    new_date = '3014-07-16T22:52:02.480108'
    mw.createdate = date
    header = mw._mets_header(new_date)
    assert header.tag == '{http://www.loc.gov/METS/}metsHdr'
    assert header.attrib['CREATEDATE'] == date
    assert header.attrib['LASTMODDATE'] == new_date
    assert header.attrib['CREATEDATE'] < header.attrib['LASTMODDATE']


def test_mdsec_identifier():
    # should be in the format 'amdSec_1'
    amdsec = mets.AMDSec()
    assert amdsec.id_string()


def test_mdwrap():
    mdwrap = mets.MDWrap('<foo/>', 'PREMIS:DUMMY')
    mdwrapped = mdwrap.serialize()

    target = '<ns0:mdWrap xmlns:ns0="http://www.loc.gov/METS/" MDTYPE="PREMIS:DUMMY"><ns0:xmlData><foo/></ns0:xmlData></ns0:mdWrap>'

    assert mdwrapped.tag == '{http://www.loc.gov/METS/}mdWrap'
    assert mdwrap.document.tag == 'foo'
    assert etree.tostring(mdwrapped) == target


def test_mdwrap_parse():
    # Wrong tag name
    bad = etree.Element('foo')
    with pytest.raises(mets.ParseError):
        mets.MDWrap.parse(bad)
    # No MDTYPE
    bad = etree.Element('{http://www.loc.gov/METS/}mdWrap')
    with pytest.raises(mets.ParseError):
        mets.MDWrap.parse(bad)
    # mdWrap has no children
    bad = etree.Element('{http://www.loc.gov/METS/}mdWrap', MDTYPE='dummy')
    with pytest.raises(mets.ParseError):
        mets.MDWrap.parse(bad)
    # xmlData has no children
    bad = etree.Element('{http://www.loc.gov/METS/}mdWrap', MDTYPE='dummy')
    etree.SubElement(bad, '{http://www.loc.gov/METS/}xmlData')
    with pytest.raises(mets.ParseError):
        mets.MDWrap.parse(bad)
    # Parses correctly
    good = etree.Element('{http://www.loc.gov/METS/}mdWrap', MDTYPE='dummy')
    xmldata = etree.SubElement(good, '{http://www.loc.gov/METS/}xmlData')
    document = etree.SubElement(xmldata, 'foo')
    mdwrap = mets.MDWrap.parse(good)
    assert mdwrap.mdtype == 'dummy'
    assert mdwrap.document == document


def test_mdref():
    mdref = mets.MDRef('path/to/file.txt', 'PREMIS:DUMMY')
    mdreffed = mdref.serialize()

    assert mdreffed.get('LOCTYPE') == 'URL'
    assert mdreffed.get('OTHERLOCTYPE') == 'SYSTEM'
    assert mdreffed.get(mets.lxmlns('xlink')+'href') == \
        'path/to/file.txt'
    assert mdreffed.get('MDTYPE') == 'PREMIS:DUMMY'


def test_mdref_parse():
    # Wrong tag name
    bad = etree.Element('foo')
    with pytest.raises(mets.ParseError):
        mets.MDRef.parse(bad)
    # No MDTYPE
    bad = etree.Element('{http://www.loc.gov/METS/}mdRef')
    with pytest.raises(mets.ParseError):
        mets.MDRef.parse(bad)
    # Parses correctly
    good = etree.Element('{http://www.loc.gov/METS/}mdRef', MDTYPE='dummy')
    good.set('{http://www.w3.org/1999/xlink}href', 'url')
    mdref = mets.MDRef.parse(good)
    assert mdref.target == 'url'
    assert mdref.mdtype == 'dummy'


def test_subsection_allowed_tags():
    with pytest.raises(ValueError):
        mets.SubSection('fakeMD', None)


def test_subsection_serialize():
    content = mets.MDWrap('<foo/>', None)
    content.serialize = lambda: etree.Element('dummy_data')
    subsection = mets.SubSection('techMD', content)
    subsection._id = 'techMD_1'

    target = '<ns0:techMD xmlns:ns0="http://www.loc.gov/METS/" ID="techMD_1" CREATED="2014-07-23T21:48:33"><dummy_data/></ns0:techMD>'

    assert etree.tostring(subsection.serialize("2014-07-23T21:48:33")) == target


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


def test_file_id():
    d = mets.FSEntry('dir', type='Directory')
    assert d.file_id() == None
    f = mets.FSEntry('level1.txt')
    with pytest.raises(mets.MetsError):
        f.file_id()
    file_uuid = str(uuid.uuid4())
    f = mets.FSEntry('level1.txt', file_uuid=file_uuid)
    assert f.file_id() == 'file-' + file_uuid


def test_group_id():
    f = mets.FSEntry('level1.txt')
    with pytest.raises(mets.MetsError):
        f.group_id()
    file_uuid = str(uuid.uuid4())
    f = mets.FSEntry('level1.txt', file_uuid=file_uuid)
    assert f.group_id() == 'Group-' + file_uuid
    derived = mets.FSEntry('level3.txt', file_uuid=str(uuid.uuid4()), derived_from=f)
    assert derived.group_id() == 'Group-' + file_uuid
    assert derived.group_id() == f.group_id()


def test_files():
    # Test collects several children deep
    f3 = mets.FSEntry('level3.txt', file_uuid=str(uuid.uuid4()))
    d2 = mets.FSEntry('dir2', type='Directory', children=[f3])
    f2 = mets.FSEntry('level2.txt', file_uuid=str(uuid.uuid4()))
    d1 = mets.FSEntry('dir1', type='Directory', children=[d2, f2])
    f1 = mets.FSEntry('level1.txt', file_uuid=str(uuid.uuid4()))
    d = mets.FSEntry('root', type='Directory', children=[d1, f1])
    mw = mets.METSWriter()
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
    f4 = mets.FSEntry('file4.txt', file_uuid=f4_uuid)
    mw.append_file(f4)
    files = mw.all_files()
    assert len(files) == 7
    assert f4 in files


def test_get_file():
    # Test collects several children deep
    f3_uuid = str(uuid.uuid4())
    f3 = mets.FSEntry('level3.txt', file_uuid=f3_uuid)
    d2 = mets.FSEntry('dir2', type='Directory', children=[f3])
    f2_uuid = str(uuid.uuid4())
    f2 = mets.FSEntry('level2.txt', file_uuid=f2_uuid)
    d1 = mets.FSEntry('dir1', type='Directory', children=[d2, f2])
    f1_uuid = str(uuid.uuid4())
    f1 = mets.FSEntry('level1.txt', file_uuid=f1_uuid)
    d = mets.FSEntry('root', type='Directory', children=[d1, f1])
    mw = mets.METSWriter()
    mw.append_file(d)
    assert mw.get_file(f3_uuid) == f3
    assert mw.get_file(f2_uuid) == f2
    assert mw.get_file(f1_uuid) == f1
    assert mw.get_file('something') == None
    f4_uuid = str(uuid.uuid4())
    f4 = mets.FSEntry('file4.txt', file_uuid=f4_uuid)
    mw.append_file(f4)
    assert mw.get_file(f4_uuid) == f4


def test_collect_mdsec_elements():
    f1 = mets.FSEntry('file1.txt', file_uuid=str(uuid.uuid4()))
    f1.amdsecs.append(mets.AMDSec())
    f1.dmdsecs.append(mets.SubSection('dmdSec', None))
    f2 = mets.FSEntry('file2.txt', file_uuid=str(uuid.uuid4()))
    f2.dmdsecs.append(mets.SubSection('dmdSec', None))
    mw = mets.METSWriter()
    elements = mw._collect_mdsec_elements([f1, f2])
    # Check ordering - dmdSec before amdSec
    assert isinstance(elements, list)
    assert len(elements) == 3
    assert isinstance(elements[0], mets.SubSection)
    assert elements[0].subsection == 'dmdSec'
    assert isinstance(elements[1], mets.SubSection)
    assert elements[1].subsection == 'dmdSec'
    assert isinstance(elements[2], mets.AMDSec)


def test_add_metadata_to_fsentry():
    f1 = mets.FSEntry('file1.txt', file_uuid=str(uuid.uuid4()))
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


def test_filesec():
    o = mets.FSEntry('objects/file1.txt', file_uuid=str(uuid.uuid4()))
    p = mets.FSEntry('objects/file1-preservation.txt', use='preservaton', file_uuid=str(uuid.uuid4()))
    o2 = mets.FSEntry('objects/file2.txt', file_uuid=str(uuid.uuid4()))
    mw = mets.METSWriter()
    element = mw._filesec([o,p,o2])
    assert isinstance(element, etree._Element)
    assert element.tag == '{http://www.loc.gov/METS/}fileSec'
    assert len(element) == 2  # 2 groups
    assert element[0].tag == '{http://www.loc.gov/METS/}fileGrp'
    assert element[0].get('USE') == 'original'
    assert element[1].tag == '{http://www.loc.gov/METS/}fileGrp'
    assert element[1].get('USE') == 'preservaton'
    # TODO test file & FLocat


def test_structmap():
    children = [
        mets.FSEntry('objects/file1.txt', file_uuid=str(uuid.uuid4())),
        mets.FSEntry('objects/file2.txt', file_uuid=str(uuid.uuid4())),
    ]
    parent = mets.FSEntry('objects', type='Directory', children=children)
    writer = mets.METSWriter()
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


def test_full_mets():
    mw = mets.METSWriter()
    file1 = mets.FSEntry('objects/object1.ext', file_uuid=str(uuid.uuid4()))
    file2 = mets.FSEntry('objects/object2.ext', file_uuid=str(uuid.uuid4()))
    file1p = mets.FSEntry('objects/object1-preservation.ext', use='preservation', file_uuid=str(uuid.uuid4()), derived_from=file1)
    file2p = mets.FSEntry('objects/object2-preservation.ext', use='preservation', file_uuid=str(uuid.uuid4()), derived_from=file2)
    children = [file1, file2, file1p, file2p]
    objects = mets.FSEntry('objects', type='Directory', children=children)
    children = [
        mets.FSEntry('transfers', type='Directory', children=[]),
        mets.FSEntry('metadata/metadata.csv', use='metadata', file_uuid=str(uuid.uuid4())),
    ]
    metadata = mets.FSEntry('metadata', type='Directory', children=children)
    children = [
        mets.FSEntry('submissionDocumentation/METS.xml', use='submissionDocumentation', file_uuid=str(uuid.uuid4())),
    ]
    sub_doc = mets.FSEntry('submissionDocumentation', type='Directory', children=children)
    children = [objects, metadata, sub_doc]
    sip = mets.FSEntry('sipname-uuid', type='Directory', children=children)
    file1.add_premis_object('<premis>object</premis>')
    file1.add_premis_event('<premis>event</premis>')
    file1.add_premis_agent('<premis>agent</premis>')
    file1.add_premis_rights('<premis>rights</premis>')

    mw.append_file(sip)
    mw.write('full_mets.xml', fully_qualified=True, pretty_print=True)

    os.remove('full_mets.xml')
