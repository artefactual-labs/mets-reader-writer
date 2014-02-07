import uuid

from lxml import etree
import mets


def test_mets_root():
    mw = mets.METSWriter()
    root = mw._document_root()
    location = "http://www.loc.gov/METS/ " + \
        "http://www.loc.gov/standards/mets/version18/mets.xsd"
    assert root.tag == 'mets'
    assert root.attrib[mets.LXML_NAMESPACES['xsi']+'schemaLocation'] == location
    assert root.nsmap[None] == 'http://www.loc.gov/METS/'


def test_mets_header():
    mw = mets.METSWriter()
    header = mw._mets_header()
    assert header.tag == 'metsHdr'
    assert header.attrib['CREATEDATE']


def test_mdsec_identifier():
    # should be in the format 'amdSec_1'
    amdsec = mets.AMDSec('foo', 'techMD')
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
    assert mdreffed.get(mets.LXML_NAMESPACES['xlink']+'href') == \
        'path/to/file.txt'
    assert mdreffed.get('MDTYPE') == 'PREMIS:DUMMY'


def test_mdsec_list_production():
    mw = mets.METSWriter()
    xml = mets.MDWrap('<foo/>', 'techMD').serialize()
    amdsec = mets.AMDSec(xml, 'techMD')
    mw.amdsecs.append(amdsec)
    elements = mw._mdsec_elements()

    assert isinstance(elements, list)
    assert len(elements) == 1
    assert isinstance(elements[0], etree._Element)
    assert elements[0].tag == 'amdSec'

    xml2 = mets.MDWrap('<bar/>', 'digiProvMD').serialize()
    dmdsec = mets.DMDSec(xml2, 'digiProvMD')
    mw.dmdsecs.append(dmdsec)
    elements = mw._mdsec_elements()

    assert len(elements) == 2
    assert elements[1].tag == 'dmdSec'


def test_structmap():
    children = [
        mets.FSEntry('file1.txt', id='file-'+str(uuid.uuid4())),
        mets.FSEntry('file2.txt', id='file-'+str(uuid.uuid4())),
    ]
    parent = mets.FSEntry('objects', type='directory', children=children)
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
