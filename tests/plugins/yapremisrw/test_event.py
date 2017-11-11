from lxml import etree
import pytest
from unittest import TestCase

import metsrw
import metsrw.plugins.yapremisrw as premisrw


class TestPremisEvent(TestCase):
    """ Test Event class. """

    def test_fromfile(self):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse('fixtures/complete_mets_2.xml', parser=parser)

        xml_data_el = root.find("mets:amdSec[@ID='amdSec_5']/" +
                                "mets:digiprovMD[@ID='digiprovMD_35']/" +
                                "mets:mdWrap/" +
                                "mets:xmlData", namespaces=metsrw.NAMESPACES)
        event_el = xml_data_el.find("premis:event",
                                    namespaces=premisrw.NAMESPACES)

        # Test misc. properties
        premis_event = premisrw.Event.parse(event_el)
        assert premis_event.identifier_type == 'UUID'
        assert premis_event.identifier_value == 'daed73e2-3825-49ad-8460-6f978b19b582'
        assert premis_event.event_type == 'validation'
        assert premis_event.event_datetime == '2015-10-23T23:20:37'
        assert premis_event.detail == 'program="JHOVE"; version="1.6"'

        # Test outcomes
        assert premis_event.outcomes is not None
        assert len(premis_event.outcomes) == 1
        assert premis_event.outcomes[0]['outcome'] == 'pass'
        assert premis_event.outcomes[0]['details'] is not None
        assert len(premis_event.outcomes[0]['details']) == 1
        assert premis_event.outcomes[0]['details'][0][
            'note'] == (
                'format="TIFF"; version="4.0"; result="Well-Formed and valid"')
        assert premis_event.outcomes[0]['details'][0]['extensions'][0].find(
            'info').text == 'Example event outcome detail extension'

        # Test linking agent parsing
        assert premis_event.linking_agent_identifiers is not None
        assert len(premis_event.linking_agent_identifiers) == 3
        assert premis_event.linking_agent_identifiers[0]['identifier_type'] == 'Archivematica user pk'
        assert premis_event.linking_agent_identifiers[0]['identifier_value'] == '1'
        assert premis_event.linking_agent_identifiers[0]['roles'] is not None
        assert premis_event.linking_agent_identifiers[0]['roles'][0] == 'Preserver'

        # Test linking object parsing
        assert premis_event.linking_object_identifiers is not None
        assert len(premis_event.linking_object_identifiers) == 1
        assert premis_event.linking_object_identifiers[0]['identifier_type'] == 'Example Object Identifier Type'
        assert premis_event.linking_object_identifiers[0]['identifier_value'] == 'Example Object Identifier Value'
        assert premis_event.linking_object_identifiers[0]['roles'] is not None
        assert premis_event.linking_object_identifiers[0]['roles'][0] == 'Example Object Role'

    def test_object_construction(self):
        with pytest.raises(premisrw.ConstructError):
            premisrw.Event(None, '72cb4af5-f1ce-478f-a7fc-0bcdd21267a3',
                           'Creation', '2015-10-23T23:20:37', None, None, [], [])
        with pytest.raises(premisrw.ConstructError):
            premisrw.Event('UUID', None, 'Creation', '2015-10-23T23:20:37', None, None, [], [])
        with pytest.raises(premisrw.ConstructError):
            premisrw.Event('UUID', '72cb4af5-f1ce-478f-a7fc-0bcdd21267a3', None, '2015-10-23T23:20:37', None, None, [], [])
        with pytest.raises(premisrw.ConstructError):
            premisrw.Event('UUID', '72cb4af5-f1ce-478f-a7fc-0bcdd21267a3', 'Creation', None, None, None, [], [])

    def test_parse_wrong_element(self):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse('fixtures/complete_mets_2.xml', parser=parser)

        object_el = root.find("mets:amdSec[@ID='amdSec_17']/" +
                              "mets:techMD[@ID='techMD_17']/" +
                              "mets:mdWrap/" +
                              "mets:xmlData/" +
                              "premis:object", namespaces=metsrw.NAMESPACES)

        with pytest.raises(premisrw.ParseError):
            premisrw.Event.parse(object_el)

    def test_serialization_basic(self):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse('fixtures/complete_mets_2.xml', parser=parser)

        xml_data_el = root.find("mets:amdSec[@ID='amdSec_5']/" +
                                "mets:digiprovMD[@ID='digiprovMD_35']/" +
                                "mets:mdWrap/" +
                                "mets:xmlData", namespaces=metsrw.NAMESPACES)
        fixture_event_el = xml_data_el.find("premis:event",
                                            namespaces=premisrw.NAMESPACES)

        event = premisrw.Event.parse(fixture_event_el)
        el = event.serialize()
        assert el.tag == '{}event'.format(premisrw.lxmlns('premis'))
        assert el.attrib['{}schemaLocation'.format(premisrw.lxmlns('xsi'))] == premisrw.PREMIS_SCHEMA_LOCATIONS
        assert el.attrib['version'] == premisrw.PREMIS_VERSION

        type_el = el.find(premisrw.lxmlns('premis') + 'eventType')
        assert type_el is not None
        assert type_el.text == 'validation'

        date_el = el.find(premisrw.lxmlns('premis') + 'eventDateTime')
        assert date_el is not None
        assert date_el.text == '2015-10-23T23:20:37'

        detail_el = el.find(premisrw.lxmlns('premis') + 'eventDetail')
        assert detail_el is not None
        assert detail_el.text == 'program="JHOVE"; version="1.6"'
