import os

from . import exceptions
from . import utils


class Event(object):
    """
    An object representing a PREMIS object element.

    :param str event_type: Event type.
    :param str outcome: Whether an event passed or failed.
    """

    def __init__(self, event_type=None, outcome=None):
        self.event_type = event_type
        self.outcome = outcome

    @classmethod
    def parse(cls, root):
        """
        Create a new Event by parsing root.

        :param root: Element or ElementTree to be parsed into an object.
        :raises exceptions.ParseError: If the root is not event.
        """
        if root.tag != utils.lxmlns('premis') + 'event':
            raise exceptions.ParseError('Object can only parse event elements with PREMIS namespace.')

        event_type_el = root.find(utils.lxmlns('premis') + 'eventType')
        event_type = event_type_el.text if event_type_el is not None else None

        # Parse event outcome
        event_outcome_info_el = root.find(utils.lxmlns('premis') + "eventOutcomeInformation")

        if event_outcome_info_el is not None:
            event_outcome_el = event_outcome_info_el.find(utils.lxmlns('premis') + "eventOutcome")
            outcome = event_outcome_el.text if event_outcome_el is not None else None
        else:
            outcome = None

        return cls(event_type, outcome)


class Object(object):
    """
    An object representing a PREMIS object element.

    :param str filename: Filename.
    :param object characteristics: :class:`ObjectCharacteristics` instance that is part of this PREMIS object.
    :param str identifier_type: Identifier type.
    :param str identifier_value: Identifier value.
    :param str relationship_type: Relationship type.
    :param str relationship_subtype: Relationship subtype.
    """

    def __init__(self, filename=None, characteristics=None, identifier_type=None, identifier_value=None, relationship_type=None, relationship_subtype=None):
        self.filename = filename
        self.characteristics = characteristics
        self.identifier_type = identifier_type
        self.identifier_value = identifier_value
        self.relationship_type = relationship_type
        self.relationship_subtype = relationship_subtype

    @classmethod
    def parse(cls, root):
        """
        Create a new Object by parsing root.

        :param root: Element or ElementTree to be parsed into an object.
        :raises exceptions.ParseError: If the root is not object.
        """
        if root.tag != utils.lxmlns('premis') + 'object':
            raise exceptions.ParseError('Object can only parse object elements with PREMIS namespace.')

        filename = os.path.basename(root.find(utils.lxmlns('premis') + "originalName").text)

        # Parse characteristics
        characteristics_el = root.find(utils.lxmlns('premis') + "objectCharacteristics")
        characteristics = ObjectCharacteristics.parse(characteristics_el)

        # Parse identifier
        identifier_el = root.find(utils.lxmlns('premis') + "objectIdentifier")

        if identifier_el is not None:
            identifier_type_el = identifier_el.find(utils.lxmlns('premis') + "objectIdentifierType")
            identifier_type = identifier_type_el.text if identifier_type_el is not None else None

            identifier_value_el = identifier_el.find(utils.lxmlns('premis') + "objectIdentifierValue")
            identifier_value = identifier_value_el.text if identifier_value_el is not None else None
        else:
            identifier_type = None
            identifier_value = None

        # Parse relationship to other objects
        relationship_el = root.find(utils.lxmlns('premis') + "relationship")

        if relationship_el is not None:
            type_el = relationship_el.find(utils.lxmlns('premis') + "relationshipType")
            relationship_type = type_el.text if type_el is not None else None

            subtype_el = relationship_el.find(utils.lxmlns('premis') + "relationshipSubType")
            relationship_subtype = subtype_el.text if subtype_el is not None else None
        else:
            relationship_type = None
            relationship_subtype = None

        return cls(filename, characteristics, identifier_type, identifier_value, relationship_type, relationship_subtype)


class ObjectCharacteristics(object):
    """
    An object representing a PREMIS objectCharacteristics element.

    :param str size: File size in bytes.
    :param str format_name: Name of the file format. TODO
    :param str format_version: Version of the file form.
    :param str format_registry_name: Name of the format registry.
    :param str format_registry_key: Registry-specific format key.
    :param boolean is_mets: Whether or not the file is a METS file.
    """

    def __init__(self, size=None, format_name=None, format_version=None, format_registry_name=None, format_registry_key=None, is_mets=None):
        self.size = size
        self.format_name = format_name
        self.format_version = format_version
        self.format_registry_name = format_registry_name
        self.format_registry_key = format_registry_key
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

        size_el = root.find(utils.lxmlns('premis') + "size")
        size = size_el.text if size_el is not None else None

        # Parse format designaton
        format_el = root.find(utils.lxmlns('premis') + "format")

        designation_el = format_el.find(utils.lxmlns('premis') + "formatDesignation")

        if designation_el is not None:
            format_name_el = designation_el.find(utils.lxmlns('premis') + "formatName")
            format_name = format_name_el.text if format_name_el is not None else None

            format_version_el = root.find(utils.lxmlns('premis') + "formatVersion")
            format_version = format_version_el.text if format_version_el is not None else None
        else:
            format_name = None
            format_version = None

        # Parse format registry
        registry_el = format_el.find(utils.lxmlns('premis') + "formatRegistry")

        if registry_el is not None:
            name_el = registry_el.find(utils.lxmlns('premis') + "formatRegistryName")
            format_registry_name = name_el.text if name_el is not None else None

            key_el = registry_el.find(utils.lxmlns('premis') + "formatRegistryKey")
            format_registry_key = key_el.text if key_el is not None else None
        else:
            format_registry_name = None
            format_registry_key = None

        # Determine if object is a METS file
        mets_markup_selector = (utils.lxmlns('premis') + "objectCharacteristicsExtension/" +
                                utils.lxmlns('fits') + "fits/" +
                                utils.lxmlns('fits') + "metadata/" +
                                utils.lxmlns('fits') + "text/" +
                                utils.lxmlns('fits') + "markupLanguage")

        markup_el = root.find(mets_markup_selector)

        is_mets = markup_el is not None and markup_el.text == 'http://www.loc.gov/standards/mets/mets.xsd'

        return cls(size, format_name, format_version, format_registry_name, format_registry_key, is_mets)


def parse_file_metadata(fsentry):
    metadata = None

    if fsentry.path != 'None':
        for subsection in fsentry.amdsecs[0].subsections:
            if subsection.subsection == 'techMD' and subsection.contents.mdtype == 'PREMIS:OBJECT':
                premis_object = Object.parse(subsection.contents.document)

                if not premis_object.characteristics.is_mets:
                    metadata = {}

                    metadata['filename'] = premis_object.filename

                    if premis_object.identifier_type == 'UUID':
                        metadata['uuid'] = premis_object.identifier_value

                    if premis_object.characteristics.size is not None:
                        metadata['size'] = premis_object.characteristics.size

                    # Add file format to metadata
                    if premis_object.characteristics.format_name is not None:
                        metadata['format_name'] = premis_object.characteristics.format_name
                    if premis_object.characteristics.format_version is not None:
                        metadata['format_version'] = premis_object.characteristics.format_version
                    if premis_object.characteristics.format_registry_name == 'PRONOM':
                        metadata['pronom_id'] = premis_object.characteristics.format_registry_key

                    # Add normalization status to metadata
                    if premis_object.relationship_type == 'derivation':
                        if premis_object.relationship_subtype == 'has source':
                            metadata['derivative'] = True

                        if premis_object.relationship_subtype == 'is source of':
                            metadata['normalized'] = True

                    # Indicate whether or not a file has been validated in metadata and if it passed
                    if subsection.subsection == 'digiprovMD' and subsection.contents.mdtype == 'PREMIS:EVENT':
                        premis_event = Event.parse(subsection.contents.document)

                        if premis_event.event_type == 'validation':
                            metadata['valid'] = premis_event.outcome == "pass"

    return metadata
