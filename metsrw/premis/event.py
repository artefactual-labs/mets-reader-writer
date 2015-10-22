from collections import OrderedDict
from copy import deepcopy
from lxml import etree

from .. import exceptions
from .. import utils


class Event(object):
    """
    An object representing a PREMIS event element.

    :param str identifier_type: Identifier type.
    :param str identifier_value: Identifier value.
    :param str event_type: Event type.
    :param str event_datetime: Event date/time.
    :param str detail: Event details.
    :param list outcomes: List of dicts containing outcome data.
    :param list linking_agent_identifiers: List of dicts containing linking agent identifier data.
    :param list linking_object_identifiers: List of dicts containing linking object identifier data.
    :raises exceptions.ParseError: If the root tag is not event.
    """
    def __init__(self, identifier_type, identifier_value, event_type, event_datetime, detail=None, outcomes=None, linking_agent_identifiers=None, linking_object_identifiers=None):
        if identifier_type is None:
            raise exceptions.ConstructError('identify_type argument is required.')

        if identifier_value is None:
            raise exceptions.ConstructError('identify_value argument is required.')

        if event_type is None:
            raise exceptions.ConstructError('event_type argument is required.')

        if event_datetime is None:
            raise exceptions.ConstructError('event_datetime argument is required.')

        self.identifier_type = identifier_type
        self.identifier_value = identifier_value
        self.event_type = event_type
        self.event_datetime = event_datetime
        self.detail = detail
        self.outcomes = outcomes
        self.linking_agent_identifiers = linking_agent_identifiers
        self.linking_object_identifiers = linking_object_identifiers

    @classmethod
    def parse(cls, root):
        """
        Create a new Event by parsing root.

        :param root: Element or ElementTree to be parsed into an object.
        :raises exceptions.ParseError: If the root is not event.
        """
        if root.tag != utils.lxmlns('premis') + 'event':
            raise exceptions.ParseError('Object can only parse event elements with PREMIS namespace.')

        identifier_el = root.find("premis:eventIdentifier", namespaces=utils.NAMESPACES)

        if identifier_el is not None:
            identifier_type = identifier_el.findtext("premis:eventIdentifierType", namespaces=utils.NAMESPACES)
            identifier_value = identifier_el.findtext("premis:eventIdentifierValue", namespaces=utils.NAMESPACES)
        else:
            identifier_type = None
            identifier_value = None

        event_type = root.findtext("premis:eventType", namespaces=utils.NAMESPACES)
        event_datetime = root.findtext("premis:eventDateTime", namespaces=utils.NAMESPACES)
        detail = root.findtext("premis:eventDetail", namespaces=utils.NAMESPACES)

        outcome_info_els = root.findall("premis:eventOutcomeInformation", namespaces=utils.NAMESPACES)
        outcomes = Event._parse_outcomes(outcome_info_els)

        linking_agent_identifier_els = root.findall("premis:linkingAgentIdentifier", namespaces=utils.NAMESPACES)
        linking_agent_identifiers = Event._parse_linking_agent_identifiers(linking_agent_identifier_els)

        linking_object_identifier_els = root.findall("premis:linkingObjectIdentifier", namespaces=utils.NAMESPACES)
        linking_object_identifiers = Event._parse_linking_object_identifiers(linking_object_identifier_els)

        return cls(identifier_type, identifier_value, event_type, event_datetime, detail, outcomes, linking_agent_identifiers, linking_object_identifiers)

    @classmethod
    def _parse_outcomes(cls, outcome_information_els):
        outcomes = []

        for outcome_information_el in outcome_information_els:
            details = []

            detail_els = outcome_information_el.findall("premis:eventOutcomeDetail", namespaces=utils.NAMESPACES)

            if detail_els is not None:
                for detail_el in detail_els:
                    extensions = detail_el.findall("premis:eventOutcomeDetailExtension", namespaces=utils.NAMESPACES)

                    details.append({
                        'note': detail_el.findtext("premis:eventOutcomeDetailNote", namespaces=utils.NAMESPACES),
                        'extensions': extensions
                    })

            outcomes.append({
                'outcome': outcome_information_el.findtext("premis:eventOutcome", namespaces=utils.NAMESPACES),
                'details': details
            })

        return outcomes

    @classmethod
    def _parse_linking_agent_identifiers(cls, identifier_els):
        identifiers = []

        for identifier in identifier_els:
            roles = []

            for role_el in identifier.findall("premis:linkingAgentRole", namespaces=utils.NAMESPACES):
                role = role_el.text if role_el is not None else None
                if role is not None:
                    roles.append(role)

            identifiers.append({
                'identifier_type': identifier.findtext("premis:linkingAgentIdentifierType", namespaces=utils.NAMESPACES),
                'identifier_value': identifier.findtext("premis:linkingAgentIdentifierValue", namespaces=utils.NAMESPACES),
                'roles': roles
            })

        return identifiers

    @classmethod
    def _parse_linking_object_identifiers(cls, identifier_els):
        identifiers = []

        for identifier in identifier_els:
            roles = []

            for role_el in identifier.findall("premis:linkingObjectRole", namespaces=utils.NAMESPACES):
                role = role_el.text if role_el is not None else None
                if role is not None:
                    roles.append(role)

            identifiers.append({
                'identifier_type': identifier.findtext("premis:linkingObjectIdentifierType", namespaces=utils.NAMESPACES),
                'identifier_value': identifier.findtext("premis:linkingObjectIdentifierValue", namespaces=utils.NAMESPACES),
                'roles': roles
            })

        return identifiers

    def serialize(self):
        root = self._document_root()
        root.append(self._serialize_identifier())

        if self.event_type is not None:
            event_type_el = etree.Element(utils.lxmlns('premis') + 'eventType')
            event_type_el.text = self.event_type
            root.append(event_type_el)

        if self.event_datetime is not None:
            event_datetime_el = etree.Element(utils.lxmlns('premis') + 'eventDateTime')
            event_datetime_el.text = self.event_datetime
            root.append(event_datetime_el)

        if self.detail is not None:
            event_detail_el = etree.Element(utils.lxmlns('premis') + 'eventDetail')
            event_detail_el.text = self.detail
            root.append(event_detail_el)

        for outcome_el in self._serialize_outcomes():
            root.append(outcome_el)

        for identifier_el in self._serialize_linking_agent_identifiers():
            root.append(identifier_el)

        for identifier_el in self._serialize_linking_object_identifiers():
            root.append(identifier_el)

        return root

    def _document_root(self):
        """
        Return the premis Element for the document root.
        """
        nsmap = OrderedDict([
            ('premis', utils.NAMESPACES['premis']),
            ('xsi', utils.NAMESPACES['xsi']),
            ('mets', utils.NAMESPACES['mets']),
            ('xlink', utils.NAMESPACES['xlink'])
        ])

        attrib = OrderedDict([
            ('{}schemaLocation'.format(utils.lxmlns('xsi')), utils.PREMIS_SCHEMA_LOCATIONS),
            ('version', utils.PREMIS_VERSION)
        ])

        return etree.Element(utils.lxmlns('premis') + 'event', nsmap=nsmap, attrib=attrib)

    def _serialize_identifier(self):
        root = etree.Element(utils.lxmlns('premis') + "eventIdentifier")

        identifier_type_el = etree.Element(utils.lxmlns('premis') + "eventIdentifierType")
        identifier_type_el.text = self.identifier_type
        root.append(identifier_type_el)

        identifier_value_el = etree.Element(utils.lxmlns('premis') + "eventIdentifierValue")
        identifier_value_el.text = self.identifier_value
        root.append(identifier_value_el)

        return root

    def _serialize_outcomes(self):
        outcome_info_els = []

        if self.outcomes is not None:
            for outcome in self.outcomes:
                outcome_info_el = etree.Element(utils.lxmlns('premis') + "eventOutcomeInformation")

                outcome_el = etree.Element(utils.lxmlns('premis') + "eventOutcome")
                outcome_el.text = outcome['outcome']
                outcome_info_el.append(outcome_el)

                if outcome['details'] is not None:
                    for detail in outcome['details']:
                        detail_el = etree.Element(utils.lxmlns('premis') + "eventOutcomeDetail")

                        utils.append_text_as_element_if_not_none(detail_el, detail['note'], 'premis', 'eventOutcomeDetailNote')

                        if detail['extensions'] is not None:
                            for extension_el in detail['extensions']:
                                detail_el.append(deepcopy(extension_el))

                        outcome_info_el.append(detail_el)

                outcome_info_els.append(outcome_info_el)

        return outcome_info_els

    def _serialize_linking_agent_identifiers(self):
        identifiers = []

        if self.linking_agent_identifiers is not None:
            for identifier in self.linking_agent_identifiers:
                identifier_el = etree.Element(utils.lxmlns('premis') + "linkingAgentIdentifier")

                utils.append_text_as_element_if_not_none(identifier_el, identifier['identifier_type'], 'premis', 'linkingAgentIdentifierType')
                utils.append_text_as_element_if_not_none(identifier_el, identifier['identifier_value'], 'premis', 'linkingAgentIdentifierValue')

                if identifier['roles'] is not None:
                    for role in identifier['roles']:
                        utils.append_text_as_element_if_not_none(identifier_el, role, 'premis', 'linkingAgentRole')

                identifiers.append(identifier_el)

        return identifiers

    def _serialize_linking_object_identifiers(self):
        identifiers = []

        if self.linking_object_identifiers is not None:
            for identifier in self.linking_object_identifiers:
                identifier_el = etree.Element(utils.lxmlns('premis') + "linkingObjectIdentifier")

                utils.append_text_as_element_if_not_none(identifier_el, identifier['identifier_type'], 'premis', 'linkingObjectIdentifierType')
                utils.append_text_as_element_if_not_none(identifier_el, identifier['identifier_value'], 'premis', 'linkingObjectIdentifierValue')

                if identifier['roles'] is not None:
                    for role in identifier['roles']:
                        utils.append_text_as_element_if_not_none(identifier_el, role, 'premis', 'linkingObjectRole')

                identifiers.append(identifier_el)

        return identifiers
