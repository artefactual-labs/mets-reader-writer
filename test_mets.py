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

    target = '<mdRef xmlns:ns0="http://www.w3.org/1999/xlink" OTHERLOCTYPE="SYSTEM" ns0:href="path/to/file.txt" MIMETYPE="text/plain" LOCTYPE="URL" MDTYPE="PREMIS:DUMMY"/>'
    assert etree.tostring(mdreffed) == target


def test_mdsec_list_production():
    mw = mets.METSWriter()
    xml = mets.MDWrap('<foo/>', 'techMD')
    amdsec = mets.AMDSec(xml, 'techMD')
    mw.amdsecs.append(amdsec)
    elements = mw._mdsec_elements()

    assert isinstance(elements, list)
    assert len(elements) == 1
    assert isinstance(elements[0], etree._Element)
    assert elements[0].tag == 'amdSec'

    xml2 = mets.MDWrap('<bar/>', 'digiProvMD')
    dmdsec = mets.DMDSec(xml2, 'digiProvMD')
    mw.dmdsecs.append(dmdsec)
    elements = mw._mdsec_elements()

    assert len(elements) == 2
    assert elements[1].tag == 'dmdSec'
