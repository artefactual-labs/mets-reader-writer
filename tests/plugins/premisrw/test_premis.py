from unittest import TestCase

import pytest

import metsrw
import metsrw.plugins.premisrw as premisrw
import tests.constants as c


class TestPREMIS(TestCase):
    """Test premis functionality ..."""

    def test_roundtrip(self):
        """Test the roundtripping of Python data to lxml's ``Element`` and back
        to Python data. The original python tuple should be identical to the
        round-tripped one.
        """
        lxml_el = premisrw.data_to_premis(c.EX_COMPR_EVT)
        data = premisrw.premis_to_data(lxml_el)
        assert data == c.EX_COMPR_EVT

    def test_premis_event_cls_data(self):
        """Tests that you can pass a Python tuple as the ``data`` argument to
        ``PREMISEvent`` to construct an instance.
        """
        premis_obj = premisrw.PREMISEvent(data=c.EX_COMPR_EVT)
        lxml_el = premis_obj.serialize()
        data = premisrw.premis_to_data(lxml_el)
        assert data == c.EX_COMPR_EVT

    def test_premis_event_cls_kwargs(self):
        """You should be able to pass sanely-named kwargs to ``PREMISEvent`` on
        instantiation.
        """
        premis_obj = premisrw.PREMISEvent(
            identifier_value=c.EX_COMPR_EVT_IDENTIFIER_VALUE,
            type=c.EX_COMPR_EVT_TYPE,
            date_time=c.EX_COMPR_EVT_DATE_TIME,
            detail=c.EX_COMPR_EVT_DETAIL,
            outcome_detail_note=c.EX_COMPR_EVT_OUTCOME_DETAIL_NOTE,
            linking_agent_identifier=c.EX_COMPR_EVT_AGENTS)
        lxml_el = premis_obj.serialize()
        data = premisrw.premis_to_data(lxml_el)

        assert data == c.EX_COMPR_EVT

    def create_test_pointer_file(self):
        # 1. Get the PREMIS events and object as premisrw class instances.
        compression_event = premisrw.PREMISEvent(data=c.EX_COMPR_EVT)
        events = [compression_event]
        _, compression_program_version, archive_tool = (
            compression_event.compression_details)
        premis_object = premisrw.PREMISObject(
            xsi_type=c.EX_PTR_XSI_TYPE,
            identifier_value=c.EX_PTR_IDENTIFIER_VALUE,
            message_digest_algorithm=c.EX_PTR_MESSAGE_DIGEST_ALGORITHM,
            message_digest=c.EX_PTR_MESSAGE_DIGEST,
            size=c.EX_PTR_SIZE,
            format_name=c.EX_PTR_FORMAT_NAME,
            format_registry_key=c.EX_PTR_FORMAT_REGISTRY_KEY,
            creating_application_name=archive_tool,
            creating_application_version=compression_program_version,
            date_created_by_application=c.EX_PTR_DATE_CREATED_BY_APPLICATION)
        transform_files = compression_event.get_decompression_transform_files()
        # 2. Construct the METS pointer file
        mw = metsrw.METSDocument()
        mets_fs_entry = metsrw.FSEntry(
            path=c.EX_PTR_PATH,
            file_uuid=c.EX_PTR_IDENTIFIER_VALUE,
            use=c.EX_PTR_PACKAGE_TYPE,
            type=c.EX_PTR_PACKAGE_TYPE,
            transform_files=transform_files,
            mets_div_type=c.EX_PTR_AIP_SUBTYPE)
        mets_fs_entry.add_premis_object(premis_object.serialize())
        for event in events:
            mets_fs_entry.add_premis_event(event.serialize())
        for agent in [c.EX_AGT_1, c.EX_AGT_2]:
            mets_fs_entry.add_premis_agent(premisrw.data_to_premis(agent))
        mw.append_file(mets_fs_entry)
        return mw

    def test_full_pointer_file(self):
        """Test construction of a full METS pointer file. Assert that the
        resulting file is a valid METS file using the metsrw.validate function
        which validates both against the METS/PREMIS .xsd files and against an
        Archivematica-specific Schematron file.
        """
        mw = self.create_test_pointer_file()
        is_valid, report = metsrw.validate(
            mw.serialize(), schematron=metsrw.AM_PNTR_SCT_PATH)
        if not is_valid:
            print('Pointer file is NOT'
                  ' valid.\n{}'.format(metsrw.report_string(report)))
        assert is_valid

    def test_pointer_file_read(self):
        """Test that we can use the premisrw API to read values correctly from
        a METS/PREMIS pointer file.
        """
        mw = self.create_test_pointer_file()
        aip_fsentry = mw.get_file(file_uuid=c.EX_PTR_IDENTIFIER_VALUE)
        for po in aip_fsentry.get_premis_objects():
            assert isinstance(po, premisrw.PREMISObject)
        for pe in aip_fsentry.get_premis_events():
            assert isinstance(pe, premisrw.PREMISEvent)
        for pa in aip_fsentry.get_premis_agents():
            assert isinstance(pa, premisrw.PREMISAgent)

        package_subtype = aip_fsentry.mets_div_type
        assert package_subtype == c.EX_PTR_AIP_SUBTYPE

        compression_event = [pe for pe in aip_fsentry.get_premis_events()
                             if pe.event_type == 'compression'][0]
        outcome_detail_note = compression_event.findtext(
            'event_outcome_information/'
            'event_outcome_detail/'
            'event_outcome_detail_note')
        assert outcome_detail_note == c.EX_COMPR_EVT_OUTCOME_DETAIL_NOTE

        premis_object = aip_fsentry.get_premis_objects()[0]
        checksum_algorithm = premis_object.message_digest_algorithm
        checksum = premis_object.message_digest
        assert checksum_algorithm == c.EX_PTR_MESSAGE_DIGEST_ALGORITHM
        assert checksum == c.EX_PTR_MESSAGE_DIGEST

        premis_agents = aip_fsentry.get_premis_agents()
        for pa in premis_agents:
            assert pa.identifier_type in (
                c.EX_AGT_1_IDENTIFIER_TYPE, c.EX_AGT_2_IDENTIFIER_TYPE)
            assert pa.identifier_value in (
                c.EX_AGT_1_IDENTIFIER_VALUE, c.EX_AGT_2_IDENTIFIER_VALUE)
            assert pa.name in (c.EX_AGT_1_NAME, c.EX_AGT_2_NAME)
            assert pa.type in (c.EX_AGT_1_TYPE, c.EX_AGT_2_TYPE)
            assert pa._data in [c.EX_AGT_1, c.EX_AGT_2]

    def test_premis_element_equality(self):
        premis_agent_1 = premisrw.PREMISAgent(data=c.EX_AGT_1)
        premis_agent_1_copy = premisrw.PREMISAgent(data=c.EX_AGT_1)
        premis_agent_2 = premisrw.PREMISAgent(data=c.EX_AGT_2)
        assert c.EX_AGT_1 != c.EX_AGT_2
        assert premis_agent_1 != premis_agent_2
        assert premis_agent_1 == premis_agent_1_copy
        assert premis_agent_1 == c.EX_AGT_1
        assert c.EX_AGT_1 in [premis_agent_1, premis_agent_1_copy]

    def test_dynamic_attrs(self):
        """Tests that dynamic attribute accession works correctly on
        PREMISElement subclasses. This allows us to use the output of the
        ``generate_data`` abstract method to dynamically create accessors for
        PREMIS entities, e.g., ``PREMISObject().identifier_value`` and
        ``PREMISObject().object_identifier_value`` should both return the value
        of the element at 'object_identifier/object_identifier_value' even
        though ``PREMISObject`` does not explicitly define either of those
        attributes.
        """
        compression_event = premisrw.PREMISEvent(data=c.EX_COMPR_EVT)
        _, compression_program_version, archive_tool = (
            compression_event.compression_details)
        inhibitors1 = (
            'inhibitors',
            ('inhibitorType', 'GPG'),
            ('inhibitorTarget', 'All content'))
        premis_object = premisrw.PREMISObject(
            xsi_type=c.EX_PTR_XSI_TYPE,
            identifier_value=c.EX_PTR_IDENTIFIER_VALUE,
            message_digest_algorithm=c.EX_PTR_MESSAGE_DIGEST_ALGORITHM,
            message_digest=c.EX_PTR_MESSAGE_DIGEST,
            size=c.EX_PTR_SIZE,
            format_name=c.EX_PTR_FORMAT_NAME,
            format_registry_key=c.EX_PTR_FORMAT_REGISTRY_KEY,
            creating_application_name=archive_tool,
            creating_application_version=compression_program_version,
            date_created_by_application=c.EX_PTR_DATE_CREATED_BY_APPLICATION,
            inhibitors=[inhibitors1])
        assert premis_object.format_name == c.EX_PTR_FORMAT_NAME
        assert premis_object.identifier_value == c.EX_PTR_IDENTIFIER_VALUE
        assert premis_object.object_identifier_value == c.EX_PTR_IDENTIFIER_VALUE
        assert premis_object.message_digest == c.EX_PTR_MESSAGE_DIGEST
        assert premis_object.object_characteristics__fixity__message_digest == c.EX_PTR_MESSAGE_DIGEST

        # A partial path to a leaf element is not a valid accessor:
        with pytest.raises(AttributeError):
            premis_object.fixity__message_digest

        # XML attribute accessors
        assert premis_object.xsi_type == c.EX_PTR_XSI_TYPE  # namespaced
        assert premis_object.xsi__type == c.EX_PTR_XSI_TYPE  # namespaced
        assert premis_object.type == c.EX_PTR_XSI_TYPE  # not namespaced
        assert premis_object.xsi_schema_location == (
            premisrw.PREMIS_META['xsi:schema_location'])

        assert compression_event.event_type == c.EX_COMPR_EVT_TYPE
        assert compression_event.type == c.EX_COMPR_EVT_TYPE
        assert compression_event.event_detail == c.EX_COMPR_EVT_DETAIL
        assert compression_event.detail == c.EX_COMPR_EVT_DETAIL

        premis_agent_1 = premisrw.PREMISAgent(data=c.EX_AGT_1)
        assert premis_agent_1.name == c.EX_AGT_1_NAME
        assert premis_agent_1.type == c.EX_AGT_1_TYPE
        assert premis_agent_1.identifier_type == c.EX_AGT_1_IDENTIFIER_TYPE
        assert premis_agent_1.identifier_value == c.EX_AGT_1_IDENTIFIER_VALUE
        assert premis_agent_1.agent_name == c.EX_AGT_1_NAME
        assert premis_agent_1.agent_type == c.EX_AGT_1_TYPE
        assert premis_agent_1.agent_identifier_type == c.EX_AGT_1_IDENTIFIER_TYPE
        assert premis_agent_1.agent_identifier_value == c.EX_AGT_1_IDENTIFIER_VALUE
        assert premis_agent_1.agent_identifier__agent_identifier_type == c.EX_AGT_1_IDENTIFIER_TYPE
        with pytest.raises(AttributeError):
            premis_agent_1.agent_identifier__agent_name

    def test_encryption_event(self):
        encryption_event = premisrw.PREMISEvent(data=c.EX_ENCR_EVT)
        decr_tf = encryption_event.get_decryption_transform_file()
        assert decr_tf['algorithm'] == 'GPG'
        assert decr_tf['order'] == '1'
        assert decr_tf['type'] == 'decryption'

    def test_attr_get_set(self):
        compression_event = premisrw.PREMISEvent(data=c.EX_COMPR_EVT)
        _, compression_program_version, archive_tool = (
            compression_event.compression_details)
        INHIBITORS = (
            (
                'inhibitors',
                ('inhibitor_type', 'GPG'),
                ('inhibitor_target', 'All content')
            ),
            (
                'inhibitors',
                ('inhibitor_type', 'Password protection'),
                ('inhibitor_target', 'Function: Play')
            )
        )

        old_premis_object = premisrw.PREMISObject(
            xsi_type=c.EX_PTR_XSI_TYPE,
            identifier_value=c.EX_PTR_IDENTIFIER_VALUE,
            message_digest_algorithm=c.EX_PTR_MESSAGE_DIGEST_ALGORITHM,
            message_digest=c.EX_PTR_MESSAGE_DIGEST,
            size=c.EX_PTR_SIZE,
            format_name=c.EX_PTR_FORMAT_NAME,
            format_registry_key=c.EX_PTR_FORMAT_REGISTRY_KEY,
            creating_application_name=archive_tool,
            creating_application_version=compression_program_version,
            date_created_by_application=c.EX_PTR_DATE_CREATED_BY_APPLICATION,
            relationship=c.EX_RELATIONSHIP_1)
        assert old_premis_object.relationship == (c.EX_RELATIONSHIP_1,)
        new_composition_level = str(
            int(old_premis_object.composition_level) + 1)

        new_premis_object = premisrw.PREMISObject(
            xsi_type=old_premis_object.xsi_type,
            identifier_value=old_premis_object.identifier_value,
            message_digest_algorithm=old_premis_object.message_digest_algorithm,
            message_digest=old_premis_object.message_digest,
            size=old_premis_object.size,
            format_name=old_premis_object.format_name,
            format_registry_key=old_premis_object.format_registry_key,
            creating_application_name=old_premis_object.creating_application_name,
            creating_application_version=old_premis_object.creating_application_version,
            date_created_by_application=old_premis_object.date_created_by_application,
            # New attributes:
            relationship=[old_premis_object.relationship[0].data,
                          c.EX_RELATIONSHIP_2],
            inhibitors=INHIBITORS,
            composition_level=new_composition_level)

        for attr in ('xsi_type', 'identifier_value',
                     'message_digest_algorithm', 'message_digest', 'size',
                     'format_name', 'format_registry_key',
                     'creating_application_name',
                     'creating_application_version',
                     'date_created_by_application'):
            assert getattr(old_premis_object, attr) == getattr(new_premis_object, attr)
        assert not old_premis_object.inhibitors
        assert new_premis_object.inhibitors == INHIBITORS
        assert old_premis_object.composition_level == '1'
        assert new_premis_object.composition_level == new_composition_level
        assert (old_premis_object.relationship[0], c.EX_RELATIONSHIP_2) == (
            new_premis_object.relationship)

        # Here are two ways to create a new PREMIS:OBJECT that's just like an
        # old one.

        # 1. Just pass in its data via the data kw
        new_premis_object = premisrw.PREMISObject(
            data=old_premis_object.data)
        assert new_premis_object == old_premis_object

        # 2. ...
        new_premis_object = premisrw.PREMISObject(
            xsi_type=old_premis_object.xsi_type,
            object_identifier=old_premis_object.find('object_identifier'),
            object_characteristics=old_premis_object.find('object_characteristics'),
            relationship=old_premis_object.find('relationship'))
        assert new_premis_object == old_premis_object

        new_relationships = [
            r.data for r in old_premis_object.findall('relationship')]
        new_relationships.append(c.EX_RELATIONSHIP_2)
        new_premis_object = premisrw.PREMISObject(
            xsi_type=old_premis_object.xsi_type,
            object_identifier=old_premis_object.find('object_identifier'),
            object_characteristics=old_premis_object.find('object_characteristics'),
            relationship=new_relationships)
        assert new_premis_object.object_identifier == old_premis_object.object_identifier
        assert new_premis_object.object_characteristics == old_premis_object.object_characteristics
        assert new_premis_object.relationship != old_premis_object.relationship
        assert old_premis_object.find('relationship') in new_premis_object.findall('relationship')

    def test_dynamic_class_generation(self):
        """Tests that PREMISRW's dynamic class generation works. This
        functionality dynamically creates a ``PREMISElement`` sub-class for the
        tuples that would otherwise be returned for non-scalar return values of
        attribute access on instances of ``PREMISObject``, etc. Makes the
        following assertions true::

            >>> relationship = premis_object.relationship[0]
            >>> assert isinstance(relationship, premisrw.PREMISElement)
            >>> assert not isinstance(relationship, tuple)
            >>> print(relationship.related_event_identifier_value)
            ab18d9db-716b-40e7-9929-7cd62f330d90

        This test shows how you can get the preservation derivatives for a
        given FSEntry in a METS document.
        """
        mets = metsrw.METSDocument.fromfile('fixtures/complete_mets.xml')
        orig_to_pres_deriv = {
            'objects/MARBLES.TGA':
            'objects/MARBLES-daef6f16-a13a-4a7b-bf7a-343235f6e093.tif',
            'objects/Landing_zone.jpg':
            'objects/Landing_zone-fc33fc0e-40ef-4ad9-ba52-860368e8ce5a.tif'
        }
        for fsentry in mets.all_files():
            for premis_object in fsentry.get_premis_objects():
                assert premis_object.size
                assert premis_object.message_digest
                assert premis_object.message_digest_algorithm
                for relationship in premis_object.relationship:
                    assert isinstance(relationship, premisrw.PREMISElement)
                    assert not isinstance(relationship, tuple)
                    if relationship.sub_type != 'is source of':
                        continue
                    event = fsentry.get_premis_event(
                        relationship.related_event_identifier_value)
                    if (not event) or (event.type != 'normalization'):
                        continue
                    pres_deriv_uuid = relationship.related_object_identifier_value
                    assert pres_deriv_uuid
                    pres_deriv_fsentry = mets.get_file(file_uuid=pres_deriv_uuid)
                    assert pres_deriv_fsentry.path == orig_to_pres_deriv[fsentry.path]
