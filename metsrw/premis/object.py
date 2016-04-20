from collections import OrderedDict
from copy import deepcopy
from lxml import etree
import os

from .. import exceptions
from .. import utils


class Object(object):
    """
    An object representing a PREMIS object element.

    :param list object_identifiers: List of dicts containing object identifier data.
    :param str object_category: Category.
    :param list preservation_levels: List of dicts containing preservation level data.
    :param list significate_properties: List of dicts containing significant properties data.
    :param list characteristics: List of :class:`ObjectCharacteristics` instances in this PREMIS object.
    :param str original_name: Filename.
    :param list storage: List of dicts containing storage data.
    :param list environments: List of dicts containing environment data.
    :param list signature_information: List of dicts containing signature information data.
    :param list relationships: List of dicts containing relationship data.
    :param list linking_event_identifiers: List of dicts containing linking event identifier data.
    :param list linking_intellectual_entity_identifiers: List of dicts containing linking intellectual entity identifier data.
    :param list linking_rights_statement_identifiers: List of dicts containing linking rights statement identifier data.
    :raises exceptions.ParseError: If the root element tag is not object.
    """
    def __init__(self, object_identifiers, object_category, preservation_levels=None, significant_properties=None, characteristics=None, original_name=None, storage=None, environments=None, signature_information=None, relationships=None, linking_event_identifiers=None, linking_intellectual_entity_identifiers=None, linking_rights_statement_identifiers=None, strict=True):
        if strict and object_identifiers is None:
            raise exceptions.ConstructError('object_identifiers argument is required.')

        if strict and object_category is None:
            raise exceptions.ConstructError('object_category argument is required.')

        if strict and characteristics is None:
            raise exceptions.ConstructError('characteristics argument is required.')

        self.object_identifiers = object_identifiers
        self.object_category = object_category
        self.preservation_levels = preservation_levels
        self.significant_properties = significant_properties
        self.characteristics = characteristics
        self.original_name = original_name
        self.storage = storage
        self.environments = environments
        self.signature_information = signature_information
        self.relationships = relationships
        self.linking_event_identifiers = linking_event_identifiers
        self.linking_intellectual_entity_identifiers = linking_intellectual_entity_identifiers
        self.linking_rights_statement_identifiers = linking_rights_statement_identifiers

    @classmethod
    def parse(cls, root, strict=True):
        """
        Create a new Object by parsing root.

        :param root: Element or ElementTree to be parsed into an object.
        :raises exceptions.ParseError: If the root is not object.
        """
        if root.tag != utils.lxmlns('premis') + 'object':
            raise exceptions.ParseError('Object can only parse object elements with PREMIS namespace.')

        identifier_els = root.findall("premis:objectIdentifier", namespaces=utils.NAMESPACES)
        object_identifiers = Object._parse_object_identifiers(identifier_els)
        object_category = root.findtext("premis:objectCategory", namespaces=utils.NAMESPACES)
        original_name = root.findtext("premis:originalName", namespaces=utils.NAMESPACES)

        preservation_level_els = root.findall("premis:preservationLevel", namespaces=utils.NAMESPACES)
        preservation_levels = Object._parse_preservation_levels(preservation_level_els)

        significant_properties_els = root.findall("premis:significantProperties", namespaces=utils.NAMESPACES)
        significant_properties = Object._parse_significant_properties(significant_properties_els)

        storage_els = root.findall("premis:storage", namespaces=utils.NAMESPACES)
        storage = Object._parse_storage(storage_els)

        environment_els = root.findall("premis:environment", namespaces=utils.NAMESPACES)
        environments = Object._parse_environments(environment_els)

        characteristics_els = root.findall("premis:objectCharacteristics", namespaces=utils.NAMESPACES)
        if characteristics_els is not None:
            characteristics = []
            for characteristics_el in characteristics_els:
                # Store characteristics objects as dicts for consistency
                characteristics.append(ObjectCharacteristics.parse(characteristics_el).__dict__)

        signature_information_els = root.findall("premis:signatureInformation", namespaces=utils.NAMESPACES)
        signature_information = Object._parse_signature_information(signature_information_els)

        relationship_els = root.findall("premis:relationship", namespaces=utils.NAMESPACES)
        relationships = Object._parse_relationships(relationship_els)

        event_identifier_els = root.findall('premis:linkingEventIdentifier', namespaces=utils.NAMESPACES)
        linking_event_identifiers = Object._parse_linking_event_identifiers(event_identifier_els)

        intellectual_entity_identifier_els = root.findall('premis:linkingIntellectualEntityIdentifier', namespaces=utils.NAMESPACES)
        linking_intellectual_entity_identifiers = Object._parse_linking_intellectual_entity_identifiers(intellectual_entity_identifier_els)

        linking_rights_statement_identifier_els = root.findall('premis:linkingRightsStatementIdentifier', namespaces=utils.NAMESPACES)
        linking_rights_statement_identifiers = Object._parse_linking_rights_statement_identifiers(linking_rights_statement_identifier_els)

        return cls(object_identifiers, object_category, preservation_levels, significant_properties, characteristics, original_name, storage, environments, signature_information, relationships, linking_event_identifiers, linking_intellectual_entity_identifiers, linking_rights_statement_identifiers, strict)

    @classmethod
    def _parse_object_identifiers(cls, identifier_els):
        """
        Parse a list of objectIdentifier elements and return a list of dicts.

        :param list identifier_els: List of objectIdentifier Elements to be parsed.
        """
        identifiers = []

        if identifier_els is not None:
            for identifier_el in identifier_els:
                if identifier_el is not None:
                    identifier_type = identifier_el.findtext("premis:objectIdentifierType", namespaces=utils.NAMESPACES)
                    identifier_value = identifier_el.findtext("premis:objectIdentifierValue", namespaces=utils.NAMESPACES)
                else:
                    identifier_type = None
                    identifier_value = None

                identifiers.append({
                    'type': identifier_type,
                    'value': identifier_value
                })

        return identifiers

    @classmethod
    def _parse_preservation_levels(cls, preservation_level_els):
        """
        Parse a list of preservationLevel elements and return a list of dicts.

        :param list preservation_level_els: List of preservationLevel Elements to be parsed.
        """
        preservation_levels = []

        if preservation_level_els is not None:
            for preservation_level_el in preservation_level_els:
                rationales = []

                for rationale_el in preservation_level_el.findall("premis:preservationLevelRationale", namespaces=utils.NAMESPACES):
                    rationale = rationale_el.text if rationale_el is not None else None
                    if rationale is not None:
                        rationales.append(rationale)

                date_assigned = preservation_level_el.findtext("premis:preservationLevelDateAssigned", namespaces=utils.NAMESPACES)

                preservation_levels.append({
                    'value': preservation_level_el.findtext("premis:preservationLevelValue", namespaces=utils.NAMESPACES),
                    'role': preservation_level_el.findtext("premis:preservationLevelRole", namespaces=utils.NAMESPACES),
                    'rationales': rationales,
                    'date_assigned': date_assigned
                })

        return preservation_levels

    @classmethod
    def _parse_significant_properties(cls, significant_properties_els):
        """
        Parse a list of significantProperties elements and return a list of dicts.

        :param list significant_properties_els: List of significantProperties Elements to be parsed.
        """
        significant_properties = []

        if significant_properties_els is not None:
            for significant_properties_el in significant_properties_els:
                extensions = significant_properties_el.findall("premis:significantPropertiesExtension", namespaces=utils.NAMESPACES)

                significant_properties.append({
                    'type': significant_properties_el.findtext("premis:significantPropertiesType", namespaces=utils.NAMESPACES),
                    'value': significant_properties_el.findtext("premis:significantPropertiesValue", namespaces=utils.NAMESPACES),
                    'extensions': extensions
                })

        return significant_properties

    @classmethod
    def _parse_storage(cls, storage_els):
        """
        Parse a list of storage elements and return a list of dicts.

        :param list storage_els: List of storage Elements to be parsed.
        """
        storage = []

        if storage_els is not None:
            for storage_el in storage_els:
                content_location_el = storage_el.find("premis:contentLocation", namespaces=utils.NAMESPACES)

                if content_location_el is not None:
                    location_type = content_location_el.findtext("premis:contentLocationType", namespaces=utils.NAMESPACES)
                    location_value = content_location_el.findtext("premis:contentLocationValue", namespaces=utils.NAMESPACES)
                else:
                    location_type = None
                    location_value = None

                medium = storage_el.findtext("premis:storageMedium", namespaces=utils.NAMESPACES)

                storage.append({
                    'location_type': location_type,
                    'location_value': location_value,
                    'medium': medium
                })

        return storage

    @classmethod
    def _parse_environments(cls, environment_els):
        """
        Parse a list of environment elements and return a list of dicts.

        :param list environment_els: List of environment Elements to be parsed.
        """
        environments = []

        if environment_els is not None:
            for environment_el in environment_els:
                characteristic = environment_el.findtext("premis:environmentCharacteristic", namespaces=utils.NAMESPACES)

                purposes = []

                for purpose_el in environment_el.findall("premis:environmentPurpose", namespaces=utils.NAMESPACES):
                    purpose = purpose_el.text if purpose_el is not None else None
                    if purpose is not None:
                        purposes.append(purpose)

                notes = []

                for note_el in environment_el.findall("premis:environmentNote", namespaces=utils.NAMESPACES):
                    note = note_el.text if note_el is not None else None
                    if note is not None:
                        notes.append(note)

                dependencies = []

                for dependency_el in environment_el.findall("premis:dependency", namespaces=utils.NAMESPACES):
                    names = []

                    for name_el in dependency_el.findall("premis:dependencyName", namespaces=utils.NAMESPACES):
                        name = name_el.text if name_el is not None else None
                        if name is not None:
                            names.append(name)

                    identifiers = []

                    for identifier_el in dependency_el.findall("premis:dependencyIdentifier", namespaces=utils.NAMESPACES):
                        identifiers.append({
                            'type': identifier_el.findtext("premis:dependencyIdentifierType", namespaces=utils.NAMESPACES),
                            'value': identifier_el.findtext("premis:dependencyIdentifierValue", namespaces=utils.NAMESPACES)
                        })

                    dependencies.append({
                        'names': names,
                        'identifiers': identifiers
                    })

                software = []

                for software_el in environment_el.findall("premis:software", namespaces=utils.NAMESPACES):
                    other_informations = []

                    other_information_els = software_el.findall("premis:swOtherInformation", namespaces=utils.NAMESPACES)
                    for other_information_el in other_information_els:
                        other_information = other_information_el.text if other_information_el is not None else None
                        if other_information is not None:
                            other_informations.append(other_information)

                    sw_dependencies = []
                    for sw_dependency_el in software_el.findall("premis:swDependency", namespaces=utils.NAMESPACES):
                        sw_dependency = sw_dependency_el.text if sw_dependency_el is not None else None
                        if sw_dependency is not None:
                            sw_dependencies.append(sw_dependency)

                    software.append({
                        'swname': software_el.findtext("premis:swName", namespaces=utils.NAMESPACES),
                        'swversion': software_el.findtext("premis:swVersion", namespaces=utils.NAMESPACES),
                        'swtype': software_el.findtext("premis:swType", namespaces=utils.NAMESPACES),
                        'other_information': other_informations,
                        'dependencies': sw_dependencies
                    })

                hardware = []
                hardware_els = environment_el.findall("premis:hardware", namespaces=utils.NAMESPACES)
                for hardware_el in hardware_els:
                    other_informations = []

                    for other_information_el in hardware_el.findall("premis:hwOtherInformation", namespaces=utils.NAMESPACES):
                        other_information = other_information_el.text if other_information_el is not None else None
                        if other_information is not None:
                            other_informations.append(other_information)

                    hardware.append({
                        'hwname': hardware_el.findtext("premis:hwName", namespaces=utils.NAMESPACES),
                        'hwtype': hardware_el.findtext("premis:hwType", namespaces=utils.NAMESPACES),
                        'other_information': other_informations
                    })

                extensions = environment_el.findall("premis:environmentExtension", namespaces=utils.NAMESPACES)

                environments.append({
                    'characteristic': characteristic,
                    'purposes': purposes,
                    'notes': notes,
                    'dependencies': dependencies,
                    'software': software,
                    'hardware': hardware,
                    'extensions': extensions
                })

        return environments

    @classmethod
    def _parse_signature_information(cls, signature_information_els):
        """
        Parse a list of signatureInformation elements and return a list of dicts.

        :param list signature_information_els: List of signatureInformation Elements to be parsed.
        """
        signature_information = []

        if signature_information_els is not None:
            for signature_information_el in signature_information_els:
                signatures = []

                for signature_el in signature_information_el.findall("premis:signature", namespaces=utils.NAMESPACES):
                    properties = []
                    property_els = signature_el.findall("premis:signatureProperties", namespaces=utils.NAMESPACES)

                    for property_el in property_els:
                        properties.append(property_el.text)

                    signatures.append({
                        'encoding': signature_el.findtext("premis:signatureEncoding", namespaces=utils.NAMESPACES),
                        'signer': signature_el.findtext("premis:signer", namespaces=utils.NAMESPACES),
                        'method': signature_el.findtext("premis:signatureMethod", namespaces=utils.NAMESPACES),
                        'value': signature_el.findtext("premis:signatureValue", namespaces=utils.NAMESPACES),
                        'validation_rules': signature_el.findtext("premis:signatureValidationRules", namespaces=utils.NAMESPACES),
                        'properties': properties,
                        'key_info': signature_el.findtext("premis:keyInformation", namespaces=utils.NAMESPACES)
                    })

                extensions = signature_information_el.findall("premis:signatureInformationExtension", namespaces=utils.NAMESPACES)

                signature_information.append({
                    'signatures': signatures,
                    'extensions': extensions
                })

        return signature_information

    @classmethod
    def _parse_relationships(cls, relationship_els):
        """
        Parse a list of relationship elements and return a list of dicts.

        :param list relationship_els: List of relationship Elements to be parsed.
        """
        relationships = []

        if relationship_els is not None:
            for relationship_el in relationship_els:
                related_object_identification = []

                for related_object_id_el in relationship_el.findall("premis:relatedObjectIdentification", namespaces=utils.NAMESPACES):
                    related_object_identification.append({
                        'type': related_object_id_el.findtext("premis:relatedObjectIdentifierType", namespaces=utils.NAMESPACES),
                        'value': related_object_id_el.findtext("premis:relatedObjectIdentifierValue", namespaces=utils.NAMESPACES),
                        'sequence': related_object_id_el.findtext("premis:relatedObjectSequence", namespaces=utils.NAMESPACES)
                    })

                related_event_identification = []
                related_event_id_els = relationship_el.findall("premis:relatedEventIdentification", namespaces=utils.NAMESPACES)
                for related_event_id_el in related_event_id_els:
                    related_event_identification.append({
                        'type': related_event_id_el.findtext("premis:relatedEventIdentifierType", namespaces=utils.NAMESPACES),
                        'value': related_event_id_el.findtext("premis:relatedEventIdentifierValue", namespaces=utils.NAMESPACES),
                        'sequence': related_event_id_el.findtext("premis:relatedEventSequence", namespaces=utils.NAMESPACES)
                    })

                relationships.append({
                    'type': relationship_el.findtext("premis:relationshipType", namespaces=utils.NAMESPACES),
                    'subtype': relationship_el.findtext("premis:relationshipSubType", namespaces=utils.NAMESPACES),
                    'related_objects': related_object_identification,
                    'related_events': related_event_identification
                })

        return relationships

    @classmethod
    def _parse_linking_event_identifiers(cls, identifier_els):
        """
        Parse a list of linkingEventIdentifier elements and return a list of dicts.

        :param list identifier_els: List of linkingEventIdentifier Elements to be parsed.
        """
        identifiers = []

        if identifier_els is not None:
            for identifier_el in identifier_els:
                identifiers.append({
                    'type': identifier_el.findtext("premis:linkingEventIdentifierType", namespaces=utils.NAMESPACES),
                    'value': identifier_el.findtext("premis:linkingEventIdentifierValue", namespaces=utils.NAMESPACES)
                })

        return identifiers

    @classmethod
    def _parse_linking_intellectual_entity_identifiers(cls, identifier_els):
        """
        Parse a list of linkingIntellectualEntityIdentifier elements and return a list of dicts.

        :param list identifier_els: List of linkingIntellectualEntityIdentifier Elements to be parsed.
        """
        identifiers = []

        if identifier_els is not None:
            for identifier_el in identifier_els:
                identifiers.append({
                    'type': identifier_el.findtext("premis:linkingIntellectualEntityIdentifierType", namespaces=utils.NAMESPACES),
                    'value': identifier_el.findtext("premis:linkingIntellectualEntityIdentifierValue", namespaces=utils.NAMESPACES)
                })

        return identifiers

    @classmethod
    def _parse_linking_rights_statement_identifiers(cls, linking_rights_statement_identifier_els):
        """
        Parse a list of linkingRightsStatementIdentifier elements and return a list of dicts.

        :param list identifier_els: List of linkingRightsStatementIdentifier Elements to be parsed.
        """
        identifiers = []

        if linking_rights_statement_identifier_els is not None:
            for identifier_el in linking_rights_statement_identifier_els:
                identifiers.append({
                    'type': identifier_el.findtext("premis:linkingRightsStatementIdentifierType", namespaces=utils.NAMESPACES),
                    'value': identifier_el.findtext("premis:linkingRightsStatementIdentifierValue", namespaces=utils.NAMESPACES)
                })

        return identifiers

    def serialize(self):
        """
        Returns this PREMIS object serialized to an xml Element.

        :return: Element for this document
        """
        root = self._document_root()

        for identifier_el in self._serialize_object_identifiers():
            root.append(identifier_el)

        if self.object_category is not None:
            category_el = etree.Element(utils.lxmlns('premis') + 'objectCategory')
            category_el.text = self.object_category
            root.append(category_el)

        for level_el in self._serialize_preservation_levels():
            root.append(level_el)

        for properties_el in self._serialize_significant_properties():
            root.append(properties_el)

        for characteristics_el in self._serialize_object_characteristics():
            root.append(characteristics_el)

        if self.original_name is not None:
            name_el = etree.Element(utils.lxmlns('premis') + 'originalName')
            name_el.text = self.original_name
            root.append(name_el)

        for storage_el in self._serialize_storage():
            root.append(storage_el)

        for environment_el in self._serialize_environment():
            root.append(environment_el)

        for signature_info_el in self._serialize_signature_information():
            root.append(signature_info_el)

        for relationship_el in self._serialize_relationships():
            root.append(relationship_el)

        for identifier_el in self._serialize_linking_event_identifiers():
            root.append(identifier_el)

        for identifier_el in self._serialize_linking_intellectual_entity_identifiers():
            root.append(identifier_el)

        for identifier_el in self._serialize_linking_rights_statement_identifiers():
            root.append(identifier_el)

        return root

    def _document_root(self):
        """
        Return the root PREMIS object Element.
        """
        nsmap = OrderedDict([
            ('premis', utils.NAMESPACES['premis']),
            ('xsi', utils.NAMESPACES['xsi']),
            ('mets', utils.NAMESPACES['mets']),
            ('xlink', utils.NAMESPACES['xlink'])
        ])

        attrib = {
            '{}type'.format(utils.lxmlns('xsi')): 'premis:file',
            '{}schemaLocation'.format(utils.lxmlns('xsi')): utils.PREMIS_SCHEMA_LOCATIONS,
            'version': utils.PREMIS_VERSION
        }

        return etree.Element(utils.lxmlns('premis') + 'object', nsmap=nsmap, attrib=attrib)

    def _serialize_object_identifiers(self):
        identifier_els = []

        if self.object_identifiers is not None:
            for identifier in self.object_identifiers:
                identifier_el = etree.Element(utils.lxmlns('premis') + "objectIdentifier")

                utils.append_text_as_element_if_not_none(identifier_el, identifier['type'], 'premis', 'objectIdentifierType')
                utils.append_text_as_element_if_not_none(identifier_el, identifier['value'], 'premis', 'objectIdentifierValue')

                identifier_els.append(identifier_el)

        return identifier_els

    def _serialize_preservation_levels(self):
        level_els = []

        if self.preservation_levels is not None:
            for level in self.preservation_levels:
                level_el = etree.Element(utils.lxmlns('premis') + "preservationLevel")

                utils.append_text_as_element_if_not_none(level_el, level['value'], 'premis', 'preservationLevelValue')
                utils.append_text_as_element_if_not_none(level_el, level['role'], 'premis', 'preservationLevelRole')

                if level['rationales'] is not None:
                    for rationale in level['rationales']:
                        utils.append_text_as_element_if_not_none(level_el, rationale, 'premis', 'preservationLevelRationale')

                utils.append_text_as_element_if_not_none(level_el, level['date_assigned'], 'premis', 'preservationLevelDateAssigned')

                level_els.append(level_el)

        return level_els

    def _serialize_significant_properties(self):
        properties_els = []

        if self.significant_properties is not None:
            for properties in self.significant_properties:
                properties_el = etree.Element(utils.lxmlns('premis') + "significantProperties")

                utils.append_text_as_element_if_not_none(properties_el, properties['type'], 'premis', 'significantPropertiesType')
                utils.append_text_as_element_if_not_none(properties_el, properties['value'], 'premis', 'significantPropertiesValue')

                if properties['extensions'] is not None:
                    for extension_el in properties['extensions']:
                        # As these are elements, need to copy so append doesn't move them in the source element tree
                        properties_el.append(deepcopy(extension_el))

                properties_els.append(properties_el)

        return properties_els

    def _serialize_object_characteristics(self):
        characteristics_els = []

        if self.characteristics is not None:
            for characteristics in self.characteristics:
                characteristics_el = etree.Element(utils.lxmlns('premis') + "objectCharacteristics")

                utils.append_text_as_element_if_not_none(characteristics_el, characteristics['composition_level'], 'premis', 'compositionLevel')

                for item in characteristics['fixity']:
                    fixity_el = etree.Element(utils.lxmlns('premis') + "fixity")
                    utils.append_text_as_element_if_not_none(fixity_el, item['digest_algorithm'], 'premis', 'messageDigestAlgorithm')
                    utils.append_text_as_element_if_not_none(fixity_el, item['digest'], 'premis', 'messageDigest')
                    utils.append_text_as_element_if_not_none(fixity_el, item['digest_originator'], 'premis', 'messageDigestOriginator')
                    characteristics_el.append(fixity_el)

                utils.append_text_as_element_if_not_none(characteristics_el, characteristics['size'], 'premis', 'size')

                for item in characteristics['formats']:
                    format_el = etree.Element(utils.lxmlns('premis') + "format")

                    if item['name'] is not None or item['version'] is not None:
                        designation_el = etree.Element(utils.lxmlns('premis') + "formatDesignation")
                        utils.append_text_as_element_if_not_none(designation_el, item['name'], 'premis', 'formatName')
                        utils.append_text_as_element_if_not_none(designation_el, item['version'], 'premis', 'formatVersion')
                        format_el.append(designation_el)

                    if item['registry_name'] is not None or item['registry_key'] is not None or item['registry_role'] is not None:
                        registry_el = etree.Element(utils.lxmlns('premis') + "formatRegistry")
                        utils.append_text_as_element_if_not_none(registry_el, item['registry_name'], 'premis', 'formatRegistryName')
                        utils.append_text_as_element_if_not_none(registry_el, item['registry_key'], 'premis', 'formatRegistryKey')
                        utils.append_text_as_element_if_not_none(registry_el, item['registry_role'], 'premis', 'formatRegistryRole')
                        format_el.append(registry_el)

                    if item['notes'] is not None:
                        for note in item['notes']:
                            utils.append_text_as_element_if_not_none(format_el, note, 'premis', 'formatNote')

                    characteristics_el.append(format_el)

                for application in characteristics['creating_applications']:
                    application_el = etree.Element(utils.lxmlns('premis') + "creatingApplication")
                    utils.append_text_as_element_if_not_none(application_el, application['name'], 'premis', 'creatingApplicationName')
                    utils.append_text_as_element_if_not_none(application_el, application['version'], 'premis', 'creatingApplicationVersion')
                    utils.append_text_as_element_if_not_none(application_el, application['create_date'], 'premis', 'dateCreatedByApplication')
                    for extension in application['extensions']:
                        # As these are elements, need to copy so append doesn't move them in the source element tree
                        application_el.append(deepcopy(extension))

                    characteristics_el.append(application_el)

                for inhibitor in characteristics['inhibitors']:
                    inhibitors_el = etree.Element(utils.lxmlns('premis') + "inhibitors")
                    utils.append_text_as_element_if_not_none(inhibitors_el, inhibitor['type'], 'premis', 'inhibitorType')
                    for target in inhibitor['targets']:
                        utils.append_text_as_element_if_not_none(inhibitors_el, target, 'premis', 'inhibitorTarget')
                    utils.append_text_as_element_if_not_none(inhibitors_el, inhibitor['key'], 'premis', 'inhibitorKey')
                    characteristics_el.append(inhibitors_el)

                for extension in characteristics['extensions']:
                    # As these are elements, need to copy so append doesn't move them in the source element tree
                    characteristics_el.append(deepcopy(extension))

                characteristics_els.append(characteristics_el)

        return characteristics_els

    def _serialize_storage(self):
        storage_els = []

        if self.storage is not None:
            for item in self.storage:
                storage_el = etree.Element(utils.lxmlns('premis') + "storage")

                if item['location_type'] is not None or item['location_value'] is not None:
                    location_el = etree.Element(utils.lxmlns('premis') + "contentLocation")

                    if item['location_type'] is not None:
                        type_el = etree.Element(utils.lxmlns('premis') + "contentLocationType")
                        type_el.text = item['location_type']
                        location_el.append(type_el)

                    if item['location_value'] is not None:
                        value_el = etree.Element(utils.lxmlns('premis') + "contentLocationValue")
                        value_el.text = item['location_value']
                        location_el.append(value_el)

                    storage_el.append(location_el)

                if item['medium'] is not None:
                    medium_el = etree.Element(utils.lxmlns('premis') + "storageMedium")
                    medium_el.text = item['medium']
                    storage_el.append(medium_el)

                storage_els.append(storage_el)

        return storage_els

    def _serialize_environment(self):
        environment_els = []

        if self.environments is not None:
            for environment in self.environments:
                environment_el = etree.Element(utils.lxmlns('premis') + "environment")

                if environment['characteristic'] is not None:
                    characteristic_el = etree.Element(utils.lxmlns('premis') + "environmentCharacteristic")
                    characteristic_el.text = environment['characteristic']
                    environment_el.append(characteristic_el)

                if environment['purposes'] is not None:
                    for purpose in environment['purposes']:
                        purpose_el = etree.Element(utils.lxmlns('premis') + "environmentPurpose")
                        purpose_el.text = purpose
                        environment_el.append(purpose_el)

                if environment['notes'] is not None:
                    for note in environment['notes']:
                        note_el = etree.Element(utils.lxmlns('premis') + "environmentNote")
                        note_el.text = note
                        environment_el.append(note_el)

                if environment['dependencies'] is not None:
                    dependency_el = etree.Element(utils.lxmlns('premis') + "dependency")

                    for dependency in environment['dependencies']:
                        if dependency['names'] is not None:
                            for name in dependency['names']:
                                name_el = etree.Element(utils.lxmlns('premis') + "dependencyName")
                                name_el.text = name
                                dependency_el.append(name_el)

                        if dependency['identifiers'] is not None:
                            for identifier in dependency['identifiers']:
                                identifier_el = etree.Element(utils.lxmlns('premis') + "dependencyIdentifier")

                                if identifier['type'] is not None:
                                    type_el = etree.Element(utils.lxmlns('premis') + "dependencyIdentifierType")
                                    type_el.text = identifier['type']
                                    identifier_el.append(type_el)

                                if identifier['value'] is not None:
                                    value_el = etree.Element(utils.lxmlns('premis') + "dependencyIdentifierValue")
                                    value_el.text = identifier['value']
                                    identifier_el.append(value_el)

                                dependency_el.append(identifier_el)

                    environment_el.append(dependency_el)

                if environment['software'] is not None:
                    for software in environment['software']:
                        software_el = etree.Element(utils.lxmlns('premis') + "software")

                        if software['swname'] is not None:
                            name_el = etree.Element(utils.lxmlns('premis') + "swName")
                            name_el.text = software['swname']
                            software_el.append(name_el)

                        if software['swversion'] is not None:
                            version_el = etree.Element(utils.lxmlns('premis') + "swVersion")
                            version_el.text = software['swversion']
                            software_el.append(version_el)

                        if software['swtype'] is not None:
                            type_el = etree.Element(utils.lxmlns('premis') + "swType")
                            type_el.text = software['swtype']
                            software_el.append(type_el)

                        if software['other_information'] is not None:
                            for other_info in software['other_information']:
                                other_el = etree.Element(utils.lxmlns('premis') + "swOtherInformation")
                                other_el.text = other_info
                                software_el.append(other_el)

                        if software['dependencies'] is not None:
                            for dependency in software['dependencies']:
                                dependency_el = etree.Element(utils.lxmlns('premis') + "swDependency")
                                dependency_el.text = dependency
                                software_el.append(dependency_el)

                        environment_el.append(software_el)

                if environment['hardware'] is not None:
                    for hardware in environment['hardware']:
                        hardware_el = etree.Element(utils.lxmlns('premis') + "hardware")

                        if hardware['hwname'] is not None:
                            name_el = etree.Element(utils.lxmlns('premis') + "hwName")
                            name_el.text = hardware['hwname']
                            hardware_el.append(name_el)

                        if hardware['hwtype'] is not None:
                            type_el = etree.Element(utils.lxmlns('premis') + "hwType")
                            type_el.text = hardware['hwtype']
                            hardware_el.append(type_el)

                        if hardware['other_information'] is not None:
                            for other_info in hardware['other_information']:
                                other_el = etree.Element(utils.lxmlns('premis') + "hwOtherInformation")
                                other_el.text = other_info
                                hardware_el.append(other_el)

                    environment_el.append(hardware_el)

                if environment['extensions'] is not None:
                    for extension_el in environment['extensions']:
                        # As these are elements, need to copy so append doesn't move them in the source element tree
                        environment_el.append(deepcopy(extension_el))

                environment_els.append(environment_el)

        return environment_els

    def _serialize_signature_information(self):
        info_els = []

        if self.signature_information is not None:
            for info in self.signature_information:
                info_el = etree.Element(utils.lxmlns('premis') + "signatureInformation")

                for signature in info['signatures']:
                    signature_el = etree.Element(utils.lxmlns('premis') + "signature")

                    if signature['encoding'] is not None:
                        utils.append_text_as_element_if_not_none(signature_el, signature['encoding'], 'premis', 'signatureEncoding')
                        utils.append_text_as_element_if_not_none(signature_el, signature['signer'], 'premis', 'signer')
                        utils.append_text_as_element_if_not_none(signature_el, signature['method'], 'premis', 'signatureMethod')
                        utils.append_text_as_element_if_not_none(signature_el, signature['value'], 'premis', 'signatureValue')
                        utils.append_text_as_element_if_not_none(signature_el, signature['validation_rules'], 'premis', 'signatureValidationRules')

                        for property in signature['properties']:
                            utils.append_text_as_element_if_not_none(signature_el, property, 'premis', 'signatureProperties')

                        utils.append_text_as_element_if_not_none(signature_el, signature['key_info'], 'premis', 'keyInformation')

                    info_el.append(signature_el)

                for extension_el in info['extensions']:
                    # As these are elements, need to copy so append doesn't move them in the source element tree
                    info_el.append(deepcopy(extension_el))

                info_els.append(info_el)

        return info_els

    def _serialize_relationships(self):
        relationship_els = []

        if self.relationships is not None:
            for relationship in self.relationships:
                relationship_el = etree.Element(utils.lxmlns('premis') + "relationship")

                utils.append_text_as_element_if_not_none(relationship_el, relationship['type'], 'premis', 'relationshipType')
                utils.append_text_as_element_if_not_none(relationship_el, relationship['subtype'], 'premis', 'relationshipSubType')

                if relationship['related_objects'] is not None:
                    for related_object in relationship['related_objects']:
                        related_object_el = etree.Element(utils.lxmlns('premis') + "relatedObjectIdentification")
                        utils.append_text_as_element_if_not_none(related_object_el, related_object['type'], 'premis', 'relatedObjectIdentifierType')
                        utils.append_text_as_element_if_not_none(related_object_el, related_object['value'], 'premis', 'relatedObjectIdentifierValue')
                        utils.append_text_as_element_if_not_none(related_object_el, related_object['sequence'], 'premis', 'relatedObjectSequence')
                        relationship_el.append(related_object_el)

                if relationship['related_events'] is not None:
                    for related_event in relationship['related_events']:
                        related_event_el = etree.Element(utils.lxmlns('premis') + "relatedEventIdentification")
                        utils.append_text_as_element_if_not_none(related_event_el, related_event['type'], 'premis', 'relatedEventIdentifierType')
                        utils.append_text_as_element_if_not_none(related_event_el, related_event['value'], 'premis', 'relatedEventIdentifierValue')
                        utils.append_text_as_element_if_not_none(related_event_el, related_event['sequence'], 'premis', 'relatedEventSequence')
                        relationship_el.append(related_event_el)

                relationship_els.append(relationship_el)

        return relationship_els

    def _serialize_linking_event_identifiers(self):
        identifier_els = []

        if self.linking_event_identifiers is not None:
            for identifier in self.linking_event_identifiers:
                identifier_el = etree.Element(utils.lxmlns('premis') + "linkingEventIdentifier")

                utils.append_text_as_element_if_not_none(identifier_el, identifier['type'], 'premis', 'linkingEventIdentifierType')
                utils.append_text_as_element_if_not_none(identifier_el, identifier['value'], 'premis', 'linkingEventIdentifierValue')

                identifier_els.append(identifier_el)

        return identifier_els

    def _serialize_linking_intellectual_entity_identifiers(self):
        identifier_els = []

        if self.linking_intellectual_entity_identifiers is not None:
            for identifier in self.linking_intellectual_entity_identifiers:
                identifier_el = etree.Element(utils.lxmlns('premis') + "linkingIntellectualEntityIdentifier")

                utils.append_text_as_element_if_not_none(identifier_el, identifier['type'], 'premis', 'linkingIntellectualEntityIdentifierType')
                utils.append_text_as_element_if_not_none(identifier_el, identifier['value'], 'premis', 'linkingIntellectualEntityIdentifierValue')

                identifier_els.append(identifier_el)

        return identifier_els

    def _serialize_linking_rights_statement_identifiers(self):
        identifier_els = []

        if self.linking_rights_statement_identifiers is not None:
            for identifier in self.linking_rights_statement_identifiers:
                identifier_el = etree.Element(utils.lxmlns('premis') + "linkingRightsStatementIdentifier")

                utils.append_text_as_element_if_not_none(identifier_el, identifier['type'], 'premis', 'linkingRightsStatementIdentifierType')
                utils.append_text_as_element_if_not_none(identifier_el, identifier['value'], 'premis', 'linkingRightsStatementIdentifierValue')

                identifier_els.append(identifier_el)

        return identifier_els


class ObjectCharacteristics(object):
    """
    An object representing a PREMIS objectCharacteristics element.

    :param str composition_level: Composition level.
    :param list fixity: List of dicts containing fixity data.
    :param str size: File size in bytes.
    :param list formats: List of dicts containing format data.
    :param list creating_applications: List of dicts containing data about creating applications.
    :param list inhibitors: List of dicts containing inhibitor data.
    :param list exntensions: List of :class:`Element` instances for extension elements.
    :param boolean is_mets: Whether or not the file is a METS file.
    :raises exceptions.ParseError: If the root element tag is not objectCharacteristics.
    """

    def __init__(self, composition_level=None, fixity=None, size=None, formats=None, creating_applications=None, inhibitors=None, extensions=None, is_mets=None):
        self.composition_level = composition_level
        self.fixity = fixity
        self.size = size
        self.formats = formats
        self.creating_applications = creating_applications
        self.inhibitors = inhibitors
        self.extensions = extensions
        self.is_mets = is_mets

    @classmethod
    def parse(cls, root):
        """
        Create a new ObjectCharacteristics by parsing root.

        :param root: Element or ElementTree to be parsed into an object.
        :raises exceptions.ParseError: If the root is not objectCharacteristics.
        """
        if root.tag != utils.lxmlns('premis') + 'objectCharacteristics':
            raise exceptions.ParseError('ObjectCharacteristics can only parse objectCharacteristics elements with PREMIS namespace.')

        composition_level = root.findtext("premis:compositionLevel", namespaces=utils.NAMESPACES)

        fixity_els = root.findall("premis:fixity", namespaces=utils.NAMESPACES)
        fixity = ObjectCharacteristics._parse_fixity(fixity_els)

        size = root.findtext("premis:size", namespaces=utils.NAMESPACES)

        format_els = root.findall("premis:format", namespaces=utils.NAMESPACES)
        formats = ObjectCharacteristics._parse_format(format_els)

        creating_application_els = root.findall("premis:creatingApplication", namespaces=utils.NAMESPACES)
        creating_applications = ObjectCharacteristics._parse_creating_applications(creating_application_els)

        inhibitor_els = root.findall("premis:inhibitors", namespaces=utils.NAMESPACES)
        inhibitors = ObjectCharacteristics._parse_inhibitors(inhibitor_els)

        # Determine if object is a METS file
        mets_markup_selector = "premis:objectCharacteristicsExtension/fits:fits/fits:metadata/fits:text/fits:markupLanguage"

        markup_el = root.find(mets_markup_selector, namespaces=utils.NAMESPACES)

        extensions = root.findall("premis:objectCharacteristicsExtension", namespaces=utils.NAMESPACES)

        is_mets = markup_el is not None and markup_el.text == 'http://www.loc.gov/standards/mets/mets.xsd'

        return cls(composition_level, fixity, size, formats, creating_applications, inhibitors, extensions, is_mets)

    @classmethod
    def _parse_fixity(cls, fixity_els):
        fixity = []

        if fixity_els is not None:
            for fixity_el in fixity_els:
                fixity.append({
                    'digest_algorithm': fixity_el.findtext("premis:messageDigestAlgorithm", namespaces=utils.NAMESPACES),
                    "digest": fixity_el.findtext("premis:messageDigest", namespaces=utils.NAMESPACES),
                    "digest_originator": fixity_el.findtext("premis:messageDigestOriginator", namespaces=utils.NAMESPACES)
                })

        return fixity

    @classmethod
    def _parse_format(cls, format_els):
        formats = []

        if format_els is not None:
            for format_el in format_els:
                designation_el = format_el.find("premis:formatDesignation", namespaces=utils.NAMESPACES)

                if designation_el is not None:
                    format_name = designation_el.findtext("premis:formatName", namespaces=utils.NAMESPACES)
                    format_version = designation_el.findtext("premis:formatVersion", namespaces=utils.NAMESPACES)
                else:
                    format_name = None
                    format_version = None

                registry_el = format_el.find("premis:formatRegistry", namespaces=utils.NAMESPACES)

                if registry_el is not None:
                    registry_name = registry_el.findtext("premis:formatRegistryName", namespaces=utils.NAMESPACES)
                    registry_key = registry_el.findtext("premis:formatRegistryKey", namespaces=utils.NAMESPACES)
                    registry_role = registry_el.findtext("premis:formatRegistryRole", namespaces=utils.NAMESPACES)
                else:
                    registry_name = None
                    registry_key = None
                    registry_role = None

                notes = []

                note_els = format_el.findall("premis:formatNote", namespaces=utils.NAMESPACES)

                if note_els is not None:
                    for note_el in note_els:
                        notes.append(note_el.text)

                formats.append({
                    'name': format_name,
                    'version': format_version,
                    'registry_name': registry_name,
                    'registry_key': registry_key,
                    'registry_role': registry_role,
                    'notes': notes
                })

        return formats

    @classmethod
    def _parse_creating_applications(cls, creating_application_els):
        creating_applications = []

        if creating_application_els is not None:
            for creating_application_el in creating_application_els:
                extensions = creating_application_el.findall("premis:creatingApplicationExtension", namespaces=utils.NAMESPACES)

                creating_applications.append({
                    'name': creating_application_el.findtext("premis:creatingApplicationName", namespaces=utils.NAMESPACES),
                    'version': creating_application_el.findtext("premis:creatingApplicationVersion", namespaces=utils.NAMESPACES),
                    'create_date': creating_application_el.findtext("premis:dateCreatedByApplication", namespaces=utils.NAMESPACES),
                    'extensions': extensions
                })

        return creating_applications

    @classmethod
    def _parse_inhibitors(cls, inhibitor_els):
        inhibitors = []

        if inhibitor_els is not None:
            for inhibitor_el in inhibitor_els:
                targets = []
                target_els = inhibitor_el.findall("premis:inhibitorTarget", namespaces=utils.NAMESPACES)
                for target_el in target_els:
                    targets.append(target_el.text)

                inhibitors.append({
                    'type': inhibitor_el.findtext("premis:inhibitorType", namespaces=utils.NAMESPACES),
                    'key': inhibitor_el.findtext("premis:inhibitorKey", namespaces=utils.NAMESPACES),
                    'targets': targets
                })

        return inhibitors
