from lxml import etree
import pytest
from unittest import TestCase

import metsrw
import metsrw.plugins.yapremisrw as premisrw


class TestPremisObject(TestCase):
    """ Test Object class. """

    def test_fromfile(self):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse('fixtures/complete_mets_2.xml', parser=parser)

        xml_data_el = root.find("mets:amdSec[@ID='amdSec_17']/" +
                                "mets:techMD[@ID='techMD_17']/" +
                                "mets:mdWrap/" +
                                "mets:xmlData", namespaces=metsrw.NAMESPACES)
        object_el = xml_data_el.find("premis:object",
                                     namespaces=premisrw.NAMESPACES)

        # Test misc. properties
        premis_object = premisrw.Object.parse(object_el)
        assert premis_object.object_category == 'Example object category'
        assert premis_object.original_name == '%transferDirectory%objects/oakland03.jp2'
        assert premis_object.object_identifiers is not None
        assert len(premis_object.object_identifiers) == 1
        assert premis_object.object_identifiers[0]['type'] == 'UUID'
        assert premis_object.object_identifiers[0]['value'] == 'e9400f17-5535-40bf-909b-e990fb9c2037'

        # Test characteristics
        assert premis_object.characteristics[0]['composition_level'] == '0'
        assert premis_object.characteristics[0]['fixity'] is not None
        assert len(premis_object.characteristics[0]['fixity']) == 1
        assert premis_object.characteristics[0]['fixity'][0]['digest_algorithm'] == 'sha256'
        assert premis_object.characteristics[0]['fixity'][0]['digest'] == 'd10bbb2cddc343cd50a304c21e67cb9d5937a93bcff5e717de2df65e0a6309d6'
        assert premis_object.characteristics[0]['fixity'][0]['digest_originator'] == 'Example message digest originator'
        assert premis_object.characteristics[0]['size'] == '527345'
        assert premis_object.characteristics[0]['formats'] is not None
        assert len(premis_object.characteristics[0]['formats']) == 1
        assert premis_object.characteristics[0]['formats'][0]['name'] == 'JP2 (JPEG 2000 part 1)'
        assert premis_object.characteristics[0]['formats'][0]['version'] == 'Example format version'
        assert premis_object.characteristics[0]['formats'][0]['registry_name'] == 'PRONOM'
        assert premis_object.characteristics[0]['formats'][0]['registry_key'] == 'x-fmt/392'
        assert premis_object.characteristics[0]['formats'][0]['registry_role'] == 'Example registry role'
        assert premis_object.characteristics[0]['formats'][0]['notes'] is not None
        assert len(premis_object.characteristics[0]['formats'][0]['notes']) == 2
        assert premis_object.characteristics[0]['formats'][0]['notes'][0] == 'Example format note #1'
        assert premis_object.characteristics[0]['formats'][0]['notes'][1] == 'Example format note #2'
        assert premis_object.characteristics[0]['creating_applications'] is not None
        assert len(premis_object.characteristics[0]['creating_applications']) == 1
        assert premis_object.characteristics[0]['creating_applications'][0]['name'] == 'Example creating application name'
        assert premis_object.characteristics[0]['creating_applications'][0]['version'] == 'Example creating application version'
        assert premis_object.characteristics[0]['creating_applications'][0]['create_date'] == 'Example creating application create date'
        assert premis_object.characteristics[0]['creating_applications'] is not None
        assert len(premis_object.characteristics[0]['creating_applications'][0]['extensions']) == 2
        assert premis_object.characteristics[0]['creating_applications'][0]['extensions'][0].find('info').text == 'Example creating application extension #1'
        assert premis_object.characteristics[0]['creating_applications'][0]['extensions'][1].find('info').text == 'Example creating application extension #2'
        assert premis_object.characteristics[0]['inhibitors'] is not None
        assert len(premis_object.characteristics[0]['inhibitors']) == 1
        assert premis_object.characteristics[0]['inhibitors'][0]['type'] == 'Example inhibitor type'
        assert premis_object.characteristics[0]['inhibitors'][0]['key'] == 'Example inhibitor key'
        assert premis_object.characteristics[0]['inhibitors'][0]['targets'] is not None
        assert len(premis_object.characteristics[0]['inhibitors'][0]['targets']) == 2
        assert premis_object.characteristics[0]['inhibitors'][0]['targets'][0] == 'Example inhibitor target #1'
        assert premis_object.characteristics[0]['inhibitors'][0]['targets'][1] == 'Example inhibitor target #2'
        assert premis_object.characteristics[0]['extensions'] is not None
        assert len(premis_object.characteristics[0]['extensions']) == 1

        # Test signature information
        assert premis_object.signature_information is not None
        assert len(premis_object.signature_information) == 1
        assert premis_object.signature_information[0]['signatures'][0]['encoding'] == 'Example signature encoding'
        assert premis_object.signature_information[0]['signatures'][0]['signer'] == 'Example signature signer'
        assert premis_object.signature_information[0]['signatures'][0]['method'] == 'Example signature method'
        assert premis_object.signature_information[0]['signatures'][0]['value'] == 'Example signature value'
        assert premis_object.signature_information[0]['signatures'][0]['validation_rules'] == 'Example signature validation rules'
        assert premis_object.signature_information[0]['signatures'][0]['properties'] is not None
        assert len(premis_object.signature_information[0]['signatures'][0]['properties']) == 2
        assert premis_object.signature_information[0]['signatures'][0]['properties'][0] == 'Example signature property #1'
        assert premis_object.signature_information[0]['signatures'][0]['key_info'] == 'Example signature key information'
        assert len(premis_object.signature_information[0]['extensions']) == 1
        assert premis_object.signature_information[0]['extensions'][0].find('info').text == 'Example signature information extension'

        # Test relationships
        assert premis_object.relationships is not None
        assert premis_object.relationships[0]['type'] == 'derivation'
        assert premis_object.relationships[0]['subtype'] == 'is source of'
        assert premis_object.relationships[0]['related_objects'][0]['type'] == 'UUID'
        assert premis_object.relationships[0]['related_objects'][0]['value'] == '4ee4365a-70dd-4c8a-98a9-976c76096b0c'
        assert premis_object.relationships[0]['related_objects'][0]['sequence'] == 'Example related object sequence'
        assert premis_object.relationships[0]['related_events'][0]['type'] == 'UUID'
        assert premis_object.relationships[0]['related_events'][0]['value'] == 'a428bcc3-43bf-49e7-9da6-074a9d1b87eb'

        # Test preservation levels
        assert premis_object.preservation_levels is not None
        assert len(premis_object.preservation_levels) == 1
        assert premis_object.preservation_levels[0]['value'] == 'Example preservation level value'
        assert premis_object.preservation_levels[0]['role'] == 'Example preservation level role'
        assert premis_object.preservation_levels[0]['date_assigned'] == 'Example preservation level date'
        assert premis_object.preservation_levels[0]['rationales'][0] == 'Example preservation level rationale'

        # Test significant properties
        assert premis_object.significant_properties is not None
        assert len(premis_object.significant_properties) == 1
        assert premis_object.significant_properties[0]['value'] == 'Example significant property value'
        assert premis_object.significant_properties[0]['type'] == 'Example significant property type'
        assert len(premis_object.significant_properties[0]['extensions']) == 1
        assert premis_object.significant_properties[0]['extensions'][0].find("info").text == 'Example significant property extension'

        # Test storage
        assert premis_object.storage is not None
        assert len(premis_object.storage) == 1
        assert premis_object.storage[0]['location_type'] == 'Example storage content location type'
        assert premis_object.storage[0]['location_value'] == 'Example storage content location value'
        assert premis_object.storage[0]['medium'] == 'Examploe storage medium'

        # Test environment
        assert premis_object.environments is not None
        assert len(premis_object.environments) == 1
        assert premis_object.environments[0]['characteristic'] == 'Example environment characteristic'
        assert premis_object.environments[0]['purposes'][0] == 'Example environment purpose #1'
        assert premis_object.environments[0]['purposes'][1] == 'Example environment purpose #2'
        assert premis_object.environments[0]['notes'][0] == 'Example environment note #1'
        assert premis_object.environments[0]['notes'][1] == 'Example environment note #2'
        assert premis_object.environments[0]['dependencies'][0]['names'][0] == 'Example environment dependency name'
        assert premis_object.environments[0]['dependencies'][0]['identifiers'][0]['type'] == 'Example environment dependency identifier type'
        assert premis_object.environments[0]['dependencies'][0]['identifiers'][0]['value'] == 'Example environment dependency identifier value'
        assert premis_object.environments[0]['software'][0]['swname'] == 'Example environment software name'
        assert premis_object.environments[0]['software'][0]['swversion'] == 'Example environment software version'
        assert premis_object.environments[0]['software'][0]['swtype'] == 'Example environment software type'
        assert premis_object.environments[0]['software'][0]['other_information'][0] == 'Example environment software other information #1'
        assert premis_object.environments[0]['software'][0]['other_information'][1] == 'Example environment software other information #2'
        assert premis_object.environments[0]['software'][0]['dependencies'][0] == 'Example environment software dependency #1'
        assert premis_object.environments[0]['software'][0]['dependencies'][1] == 'Example environment software dependency #2'
        assert premis_object.environments[0]['hardware'][0]['hwname'] == 'Example environment hardware name'
        assert premis_object.environments[0]['hardware'][0]['hwtype'] == 'Example environment hardware type'
        assert premis_object.environments[0]['hardware'][0]['other_information'][0] == 'Example environment hardware other information #1'
        assert premis_object.environments[0]['hardware'][0]['other_information'][1] == 'Example environment hardware other information #2'
        assert premis_object.environments[0]['extensions'][0].find('info').text == 'Example environment extension #1'
        assert premis_object.environments[0]['extensions'][1].find('info').text == 'Example environment extension #2'

        # Test liking event identifiers
        assert premis_object.linking_event_identifiers is not None
        assert len(premis_object.linking_event_identifiers) == 1
        assert premis_object.linking_event_identifiers[0]['type'] == 'Example linking event identifier type'
        assert premis_object.linking_event_identifiers[0]['value'] == 'Example linking event identifier value'

        # Test linking intellectual entity identifiers
        assert premis_object.linking_intellectual_entity_identifiers is not None
        assert len(premis_object.linking_intellectual_entity_identifiers) == 1
        assert premis_object.linking_intellectual_entity_identifiers[0]['type'] == 'Example linking entity identifier type'
        assert premis_object.linking_intellectual_entity_identifiers[0]['value'] == 'Example linking entity identifier value'

        # Test linking rights statement identifiers
        assert premis_object.linking_rights_statement_identifiers is not None
        assert len(premis_object.linking_rights_statement_identifiers) == 1
        assert premis_object.linking_rights_statement_identifiers[0]['type'] == 'Example linking rights statement identifier type'
        assert premis_object.linking_rights_statement_identifiers[0]['value'] == 'Example linking rights statement identifier value'

    def test_object_construction(self):
        with pytest.raises(premisrw.ConstructError):
            premisrw.Object(None, 'Category', None, None, [])
        with pytest.raises(premisrw.ConstructError):
            premisrw.Object([], None, None, None, [])
        with pytest.raises(premisrw.ConstructError):
            premisrw.Object([], 'Category', None, None, None)

    def test_parse_wrong_element(self):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse('fixtures/complete_mets_2.xml', parser=parser)

        xml_data_el = root.find("mets:amdSec[@ID='amdSec_5']/" +
                                "mets:digiprovMD[@ID='digiprovMD_35']/" +
                                "mets:mdWrap/" +
                                "mets:xmlData", namespaces=metsrw.NAMESPACES)
        event_el = xml_data_el.find("premis:event",
                                    namespaces=premisrw.NAMESPACES)
        with pytest.raises(premisrw.ParseError):
            premisrw.Object.parse(event_el)

    def test_serialization(self):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse('fixtures/complete_mets_2.xml', parser=parser)

        xml_data_el = root.find("mets:amdSec[@ID='amdSec_17']/" +
                                "mets:techMD[@ID='techMD_17']/" +
                                "mets:mdWrap/" +
                                "mets:xmlData", namespaces=metsrw.NAMESPACES)
        fixture_object_el = xml_data_el.find("premis:object",
                                             namespaces=premisrw.NAMESPACES)

        parsed_object = premisrw.Object.parse(fixture_object_el)
        el = parsed_object.serialize()
        assert el.tag == '{}object'.format(premisrw.lxmlns('premis'))
        assert el.attrib['{}schemaLocation'.format(premisrw.lxmlns('xsi'))] == premisrw.PREMIS_SCHEMA_LOCATIONS
        assert el.attrib['version'] == premisrw.PREMIS_VERSION

        category_el = el.find(premisrw.lxmlns('premis') + 'objectCategory')
        assert category_el is not None
        assert category_el.text == 'Example object category'

        name_el = el.find(premisrw.lxmlns('premis') + 'originalName')
        assert name_el is not None
        assert name_el.text == '%transferDirectory%objects/oakland03.jp2'
