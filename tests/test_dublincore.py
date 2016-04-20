from lxml import etree
import pytest
from unittest import TestCase

import metsrw
from metsrw import utils


class TestDublinCoreXmlData(TestCase):
    """ Test DublinCoreXmlData class. """

    def test_fromfile(self):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse('fixtures/complete_mets.xml', parser=parser)

        xml_data_el = root.find("mets:dmdSec[@ID='dmdSec_1']/" +
                                "mets:mdWrap/" +
                                "mets:xmlData", namespaces=utils.NAMESPACES)

        # Test properties
        dc_object = metsrw.DublinCoreXmlData.parse(xml_data_el)
        assert dc_object.title == 'Example DC title'
        assert dc_object.creator == 'Example DC creator'
        assert dc_object.subject == 'Example DC subject'
        assert dc_object.description == 'Example DC description'
        assert dc_object.publisher == 'Example DC publisher'
        assert dc_object.contributor == 'Example DC contributor'
        assert dc_object.date == '1984-01-01'
        assert dc_object.format == 'Example DC format'
        assert dc_object.identifier == 'Example DC identifier'
        assert dc_object.source == 'Example DC source'
        assert dc_object.relation == 'Example DC relation'
        assert dc_object.language == 'en'
        assert dc_object.coverage == 'Example DC coverage'
        assert dc_object.rights == 'Example DC rights'

    def test_parse_wrong_element(self):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse('fixtures/complete_mets.xml', parser=parser)

        mdwrap_el = root.find("mets:dmdSec[@ID='dmdSec_1']/" +
                              "mets:mdWrap", namespaces=utils.NAMESPACES)

        with pytest.raises(metsrw.ParseError):
            metsrw.DublinCoreXmlData.parse(mdwrap_el)

    def test_serialization(self):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse('fixtures/complete_mets.xml', parser=parser)

        fixture_dc_el = root.find("mets:dmdSec[@ID='dmdSec_1']/" +
                                  "mets:mdWrap/" +
                                  "mets:xmlData", namespaces=utils.NAMESPACES)

        parsed_dc = metsrw.DublinCoreXmlData.parse(fixture_dc_el)
        parsed_dc_el = parsed_dc.serialize()

        fixture_dc_xml = etree.tostring(fixture_dc_el, pretty_print=True)
        parsed_dc_xml = etree.tostring(parsed_dc_el, pretty_print=True)

        assert fixture_dc_xml == parsed_dc_xml
