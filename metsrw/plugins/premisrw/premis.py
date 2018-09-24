# -*- coding: utf-8 -*-
"""PREMIS-Reader-Writer: a small PREMIS library designed to work as a plugin
for METS-reader-writer. Public functions and classes:

- data_to_premis
- premis_to_data
- PREMISObject
- PREMISEvent
- PREMISAgent

"""
__metaclass__ = type

import abc
from datetime import datetime
import pprint
from uuid import uuid4

from lxml import etree
from lxml.builder import ElementMaker
import six

from . import utils


def now():
    return datetime.utcnow().replace(microsecond=0).isoformat('T')


def uuid():
    return str(uuid4())


@six.add_metaclass(abc.ABCMeta)
class PREMISElement:
    """Abstract base class for PREMIS object, event and agent classes. These
    classes must implement ``schema`` and ``defaults`` properties. After that,
    initalization can proceed either by passing a ``data`` kwarg to the class
    or by passing keyword arguments implicit in the element tag names of
    ``self.schema``, e.g.,::

        >>> premis_obj = PREMISObject(data=('object', {...}, (...)))
        >>> premis_obj = PREMISObject(
            identifier_type='UUID',
            identifier_value='9bf6bcf8-4d77-4623-a9fb-b703365d0ffe',
            ...)

    Under the first construction approach, the tuple passed as ``data`` becomes
    the source of truth for the PREMIS element. Under the second construction
    approach, the kwargs are used to construct a ``data`` tuple that becomes
    the source of truth. This tuple can be accessed via the ``.data`` property.
    """

    def __init__(self, **kwargs):
        self.premis_el_attrs = None
        self._attrs_to_paths = None
        self._attributes = None
        self._xml_element_values = {}
        self._xml_attribute_values = {}
        data = kwargs.get('data')
        if data:
            if isinstance(data, PREMISElement):
                data = data.data
            self._data = data
            self.premis_version = _premis_version_from_data(data)
        else:
            self.premis_version = kwargs.get(
                'premis_version', utils.PREMIS_VERSION)
            self._xml_element_values = self._get_xml_element_values(kwargs)
            self._xml_attribute_values = _get_xml_attribute_values(
                kwargs, self.premis_version)
            self._data = self.generate_data()

    @property
    def data(self):
        return self._data

    @property
    def attrs_to_paths(self):
        """Return a dict that maps valid getter attributes to the simplified
        XPaths needed to get the corresponding values from ``self.data``.

        This property analyzes ``self.schema`` and sets
        ``self._attrs_to_paths`` to a dict that maps implicit getters like
        'agent_identifier_value' and 'identifier_value' to the XPaths implicit
        in ``self.schema``. In the case of ``PREMISAgent``, the above two
        getters would map to the XPath
        'agent/agent_identifier/agent_identifier_value'. ``PREMISAgent.schema``
        also implies the getters 'agent_identifier' and 'identifier', which
        both map to the XPath 'agent/agent_identifier' and which should return
        a tuple (or list thereof) instead of a string.
        """
        if self._attrs_to_paths:
            return self._attrs_to_paths
        self._attrs_to_paths = {}
        schema = self.schema
        tag = schema[0]
        attrs_to_paths_init = get_attrs_to_paths(schema)
        for attr, path in attrs_to_paths_init.items():
            if attr.startswith(tag + '_'):
                new_key = attr.replace(tag + '_', '', 1)
                self._attrs_to_paths[new_key] = path
            self._attrs_to_paths[attr] = path
            parts = path.split('/')[:-1]
            while parts:
                new_attr = parts[-1]
                new_path = '/'.join(parts)
                self._attrs_to_paths[new_attr] = new_path
                parts = parts[:-1]
        return self._attrs_to_paths

    @property
    def attributes(self):
        """Return a dict that maps normalized XML attributes to their values,
        e.g., 'xsi_schema_location' and 'schema_location' would be keys for the
        value of the xsi:schemaLocation PREMIS XML attribute.
        """
        if self._attributes:
            return self._attributes
        self._attributes = {}
        for elem in self.data:
            if isinstance(elem, dict):
                for key, val in elem.items():
                    self._attributes[key] = val
                    if ':' in key:
                        key1 = key.replace(':', '_')
                        self._attributes[key1] = val
                        key2 = key.split(':', 1)[1]
                        self._attributes[key2] = val
        return self._attributes

    def serialize(self):
        return data_to_premis(self._data, self.premis_version)

    def tostring(self, pretty_print=True):
        return etree.tostring(self.serialize(), pretty_print=pretty_print)

    def __repr__(self):
        return repr(self._data)

    def __str__(self):
        return pprint.pformat(self._data, indent=4)

    def __eq__(self, other):
        """``self.data`` is the sole source of truth for ``PREMISElement``
        instances. Thus two such instances with the same data should compare
        equal as should an instance and a tuple if the instance's data is equal
        to the tuple.
        """
        if isinstance(other, PREMISElement):
            return self.data == other.data
        return self.data == other

    def __getattr__(self, attr_name):
        """Dynamically retrieve and return the value of an attribute which is
        implicitly defined by the return value of ``self.generate_data()``. All
        leaf node element names and full paths (with forward slashes replaced
        by double underscores) are now valid accessors. For example,
        ``premis_object.message_digest`` returns
        ``premis_object.findtext('object_characteristics/fixity/message_digest')``
        as does ``premis_object.object_characteristics__fixity__message_digest``.
        Similarly, ``premis_object.xsi_type``, ``premis_object.type`` and
        ``premis_object.xsi__type`` all return the value of the XML attribute
        xsi:type.
        """
        if attr_name in self.attrs_to_paths:
            return self.find_text_or_all(self.attrs_to_paths[attr_name])
        attr_name_norm = attr_name.replace('__', '/')
        if attr_name_norm in self.attrs_to_paths.values():
            return self.find_text_or_all(attr_name_norm)
        attr_name_norm = attr_name.replace('__', ':')
        if attr_name_norm in self.attributes:
            return self.attributes[attr_name_norm]
        valid_attributes = '\n'.join(sorted(set(
            list(self.attrs_to_paths.keys()) +
            [x.replace('/', '__') for x in self.attrs_to_paths.values()] +
            list(x.replace(':', '_') for x in self.attributes.keys()))))
        raise AttributeError(
            'Instance of {} has no attribute {}. Valid attributes'
            ' are\n{}'.format(self.__class__, attr_name, valid_attributes))

    def find(self, path):
        return data_find(self._data, path)

    def findall(self, path):
        return data_find_all(self._data, path, dyn_cls=True)

    def findtext(self, path):
        return data_find_text(self._data, path)

    def find_text_or_all(self, path):
        return data_find_text_or_all(self._data, path, dyn_cls=True)

    @abc.abstractmethod
    def schema(self):
        """Return a tuple representing the schema of the PREMIS element.
        This tuple schema determines the available getters and setters (during
        initialization) of the subclass.
        """

    def generate_data(self):
        """Generate and return a tuple to assign to ``self._data``, which is
        the source of truth of the PREMIS XML element.
        Expects ``self._xml_element_values`` and ``self._xml_attribute_values`` to be dicts
        populated with XML element text values and XML attribute values,
        respectively.
        """
        return _generate_data(
            self.schema, self._xml_element_values,
            attributes=self._xml_attribute_values)

    @abc.abstractmethod
    def defaults(self):
        """Return a dict that maps implicit getter attributes (implicit in
        ``self.schema``) to default values or to callables that return default
        values. For example, see ``PREMISObject.defaults``.
        """

    def _get_xml_element_values(self, kwargs):
        """Using the user-supplied dict ``kwargs`` and the defaults returned by
        ``self.defaults``, return a dict mapping XML tag names (and paths) to
        values.
        """
        full_attrs_to_paths = {}
        xml_element_values = {}
        for attr_name, attr_path in self.attrs_to_paths.items():
            full_attrs_to_paths[attr_name] = attr_path
            full_attrs_to_paths[attr_path] = attr_path
        for attr_name, attr_path in full_attrs_to_paths.items():
            default = self.defaults.get(attr_name, self.defaults.get(attr_path, ''))
            if callable(default):
                default = default()
            val = kwargs.get(attr_name, kwargs.get(attr_path, default))
            xml_element_values[attr_name] = val
            xml_element_values[attr_path] = val
        return xml_element_values

    @classmethod
    def fromtree(cls, tree):
        """Create a PREMIS from an ``_Element``."""
        return cls(data=premis_to_data(tree))


class PREMISObject(PREMISElement):

    @property
    def defaults(self):
        return {
            'identifier_type': 'UUID',
            'identifier_value': uuid,
            'composition_level': '1',
            'format_registry_name': 'PRONOM',
            'date_created_by_application': now,
            'relationship': lambda: [],
            'inhibitors': lambda: []
        }

    @property
    def schema(self):
        related_object_identifier, related_event_identifier = (
            _get_relationship_tag_names(self.premis_version))
        return (
            'object',
            (
                'object_identifier',
                ('object_identifier_type',),
                ('object_identifier_value',),
            ),
            (
                'object_characteristics',
                ('composition_level',),
                (
                    'fixity',
                    ('message_digest_algorithm',),
                    ('message_digest',),
                ),
                ('size',),
                (
                    'format',
                    (
                        'format_designation',
                        ('format_name',),
                        ('format_version',),
                    ),
                    (
                        'format_registry',
                        ('format_registry_name',),
                        ('format_registry_key',),
                    )
                ),
                (
                    'creating_application',
                    ('creating_application_name',),
                    ('creating_application_version',),
                    ('date_created_by_application',),
                ),
                (
                    'inhibitors',
                    ('inhibitor_type',),
                    ('inhibitor_target',),
                )
            ),
            (
                'relationship',
                ('relationship_type',),
                ('relationship_sub_type',),
                (
                    related_object_identifier,
                    ('related_object_identifier_type',),
                    ('related_object_identifier_value',),
                ),
                (
                    related_event_identifier,
                    ('related_event_identifier_type',),
                    ('related_event_identifier_value',),
                ),
            ),
        )


class PREMISEvent(PREMISElement):

    @property
    def defaults(self):
        return {
            'identifier_type': 'UUID',
            'identifier_value': uuid,
            'date_time': now,
            'linking_agent_identifier': lambda: []
        }

    @property
    def schema(self):
        return (
            'event',
            (
                'event_identifier',
                ('event_identifier_type',),
                ('event_identifier_value',),
            ),
            ('event_type',),
            ('event_date_time',),
            ('event_detail',),
            (
                'event_outcome_information',
                ('event_outcome',),
                (
                    'event_outcome_detail',
                    ('event_outcome_detail_note',)
                ),
            ),
            (
                'linking_agent_identifier',
                ('linking_agent_identifier_type',),
                ('linking_agent_identifier_value',)
            )
        )

    @property
    def parsed_event_detail(self):
        """Parse and return our PREMIS eventDetail string value like::

            'program="7z"; version="9.20"; algorithm="bzip2"'

        and return a dict like::

            {'algorithm': 'bzip2', 'version': '9.20', 'program': '7z'}
        """
        return dict(
            [tuple([x.strip(' "') for x in kv.strip().split('=', 1)])
             for kv in self.event_detail.split(';')])

    # Compression Event Functionality
    # ==========================================================================

    @property
    def compression_details(self):
        """Return as a 3-tuple, this PREMIS compression event's program,
        version, and algorithm used to perform the compression.
        """
        event_type = self.findtext('event_type')
        if event_type != 'compression':
            raise AttributeError(
                'PREMIS events of type "{}" have no compression'
                ' details'.format(event_type))
        parsed_compression_event_detail = self.parsed_event_detail
        compression_program = _get_event_detail_attr(
            'program', parsed_compression_event_detail)
        compression_algorithm = _get_event_detail_attr(
            'algorithm', parsed_compression_event_detail)
        compression_program_version = _get_event_detail_attr(
            'version', parsed_compression_event_detail)
        archive_tool = {'7z': '7-Zip'}.get(
            compression_program, compression_program)
        return compression_algorithm, compression_program_version, archive_tool

    def get_decompression_transform_files(self, offset=0):
        """Returns a list of dicts representing ``<mets:transformFile>``
        elements with ``TRANSFORMTYPE="decompression"`` given
        ``compression_algorithm`` which is a comma-separated string of
        algorithms that must be used in the order provided to decompress
        the package, e.g., 'bzip2,tar' or 'lzma'.
        """
        compression_algorithm, _, _ = self.compression_details
        return [{'algorithm': algorithm,
                 'order': str(index + offset + 1),
                 'type': 'decompression'}
                for index, algorithm in enumerate(
                    compression_algorithm.split(','))]

    # Encryption Event Functionality
    # ==========================================================================

    @property
    def encryption_details(self):
        """Return as a 3-tuple, this PREMIS encryption event's program,
        version, and key used to perform the encryption.
        """
        event_type = self.findtext('event_type')
        if event_type != 'encryption':
            raise AttributeError(
                'PREMIS events of type "{}" have no encryption'
                ' details'.format(event_type))
        parsed_encryption_event_detail = self.parsed_event_detail
        encryption_program = _get_event_detail_attr(
            'program', parsed_encryption_event_detail)
        encryption_program_version = _get_event_detail_attr(
            'version', parsed_encryption_event_detail)
        encryption_key = _get_event_detail_attr(
            'key', parsed_encryption_event_detail)
        return encryption_program, encryption_program_version, encryption_key

    def get_decryption_transform_file(self):
        """Returns a dict representing a ``<mets:transformFile>`` element with
        ``TRANSFORMTYPE="decryption"``.
        """
        encryption_program, _, encryption_key = self.encryption_details
        return {'algorithm': encryption_program,
                'order': '1',
                'type': 'decryption',
                'key': encryption_key}


class PREMISAgent(PREMISElement):

    @property
    def defaults(self):
        return {}

    @property
    def schema(self):
        return (
            'agent',
            (
                'agent_identifier',
                ('agent_identifier_type',),
                ('agent_identifier_value',)
            ),
            ('agent_name',),
            ('agent_type',)
        )


def _data_to_lxml_el(data, ns, nsmap, element_maker=None, snake=True):
    """Convert tuple/list ``data`` to an ``lxml.etree._Element`` instance.
    :param tuple/list data: iterable whose first element is the snake-case
        string which is the name of the root XML element. Subsequent elements
        may be dicts (which encode XML attributes), tuples/lists (which encode
        sub-elements), or scalars (strings, ints or floats, which encode text
        under the element).
    :param str ns: the implicit namespace of all elements in the XML.
    :param dict nsmap: a dict of XML namespaces to define in the root element.
    :param ElementMaker element_maker: instance for creating XML elements.
    :returns: an ``lxml.etree._Element`` instance
    """
    if not element_maker:
        element_maker = ElementMaker(namespace=nsmap[ns], nsmap=nsmap)
    tag = data[0]
    if snake:
        camel_tag = utils.snake_to_camel(tag)
    func = getattr(element_maker, camel_tag)
    args = []
    attributes = {}
    for element in data[1:]:
        if isinstance(element, dict):
            for key, val in element.items():
                attributes[key] = val
        elif isinstance(element, (tuple, list)):
            args.append(_data_to_lxml_el(
                element, ns, nsmap, element_maker=element_maker, snake=snake))
        else:
            args.append(str(element))
    ret = func(*args)
    for attr, val in attributes.items():
        try:
            ns, attr = attr.split(':')
        except ValueError:
            ns = None
        if snake:
            attr = utils.snake_to_camel(attr)
        if ns:
            attr = '{' + nsmap[ns] + '}' + attr
            ret.attrib[attr] = val
        else:
            ret.attrib[attr] = val
    return ret


def _to_colon_ns(bracket_ns, default_ns=None, nsmap=None, snake=True):
    """Convert a namespaced tag/attribute name from explicit XML "bracket"
    notation to a more succinct Pythonic colon-separated notation using
    snake_case, e.g.,::

        >>> _to_colon_ns(
            '{info:lc/xmlns/premis-v2}objectIdentifier',
            'premis', utils.NAMESPACES)
        'object_identifier'
        >>> _to_colon_ns('{info:lc/xmlns/premis-v2}objectIdentifier')
        'premis:object_identifier'
        >>> _to_colon_ns(
            'http://www.w3.org/2001/XMLSchema-instance}schemaLocation')
        'xsi:schema_location'
    """
    parts = [x.strip('{') for x in bracket_ns.split('}')]
    if len(parts) != 2:
        return bracket_ns
    ns, var = parts
    if default_ns and nsmap:
        try:
            ns = [k for k, v in nsmap.items() if v == ns][0]
            if ns == default_ns:
                if snake:
                    return utils.camel_to_snake(var)
                return var
        except IndexError:
            pass
    if snake:
        return ':'.join([ns, utils.camel_to_snake(var)])
    return ':'.join([ns, var])


def _get_el_attributes(lxml_el, ns=None, nsmap=None):
    """Return the XML attributes of lxml ``Element`` instance lxml_el as a dict
    where namespaced attributes are represented via colon-delimiting and using
    snake case.
    """
    attrs = {}
    for attr, val in lxml_el.items():
        attr = _to_colon_ns(attr, default_ns=ns, nsmap=nsmap)
        attrs[attr] = val
    return attrs


def _lxml_el_to_data(lxml_el, ns, nsmap, snake=True):
    """Convert an ``lxml._Element`` instance to a Python tuple."""
    tag_name = _to_colon_ns(lxml_el.tag, default_ns=ns, nsmap=nsmap)
    ret = [tag_name]
    attributes = _get_el_attributes(lxml_el, ns=ns, nsmap=nsmap)
    if attributes:
        ret.append(attributes)
    for sub_el in lxml_el:
        ret.append(_lxml_el_to_data(sub_el, ns, nsmap, snake=snake))
    text = lxml_el.text
    if text:
        ret.append(text)
    return tuple(ret)


def data_to_premis(data, premis_version=utils.PREMIS_VERSION):
    """Given tuple ``data`` representing a PREMIS entity (object, event or
    agent), return an ``lxml.etree._Element`` instance. E.g.,::

        >>> p = data_to_premis((
            'event',
            utils.PREMIS_META,
            (
                'event_identifier',
                ('event_identifier_type', 'UUID'),
                ('event_identifier_value', str(uuid4()))
            )
        ))
        >>> etree.tostring(p, pretty_print=True).decode('utf8')
        '''<premis:event
            xmlns:premis="info:lc/xmlns/premis-v2"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            version="2.2"
            xsi:schemaLocation="info:lc/xmlns/premis-v2 http://www.loc.gov/standards/premis/v2/premis-v2-2.xsd">
            <premis:eventIdentifier>
                <premis:eventIdentifierType>UUID</premis:eventIdentifierType>
                <premis:eventIdentifierValue>f4b7758f-e7b2-4155-9b56-d76965849fc1</premis:eventIdentifierValue>
            </premis:eventIdentifier>
        </premis:event>'''
    """
    nsmap = utils.PREMIS_VERSIONS_MAP[premis_version]['namespaces']
    return _data_to_lxml_el(data, 'premis', nsmap)


def premis_to_data(premis_lxml_el):
    """Transform a PREMIS ``lxml._Element`` instance to a Python tuple."""
    premis_version = premis_lxml_el.get('version', utils.PREMIS_VERSION)
    nsmap = utils.PREMIS_VERSIONS_MAP[premis_version]['namespaces']
    return _lxml_el_to_data(premis_lxml_el, 'premis', nsmap)


def data_find(data, path):
    """Find and return the first element-as-tuple in tuple ``data`` using simplified
    XPath ``path``.
    """
    path_parts = path.split('/')
    try:
        sub_elm = [el for el in data if
                   isinstance(el, (tuple, list)) and
                   el[0] == path_parts[0]][0]
    except IndexError:
        return None
    else:
        if len(path_parts) > 1:
            return data_find(sub_elm, '/'.join(path_parts[1:]))
        return sub_elm


def tuple_to_schema(tuple_):
    """Convert a tuple representing an XML data structure into a schema tuple
    that can be used in the ``.schema`` property of a sub-class of
    PREMISElement.
    """
    schema = []
    for element in tuple_:
        if isinstance(element, (tuple, list)):
            try:
                if isinstance(element[1], six.string_types):
                    schema.append((element[0],))
                else:
                    schema.append(tuple_to_schema(element))
            except IndexError:
                schema.append((element[0],))
        else:
            schema.append(element)
    return tuple(schema)


def generate_element_class(tuple_instance):
    """Dynamically create a sub-class of PREMISElement given
    ``tuple_instance``, which is a tuple representing an XML data structure.
    """
    schema = tuple_to_schema(tuple_instance)

    def defaults(self):
        return {}

    def schema_getter(self):
        return schema

    new_class_name = 'PREMIS{}Element'.format(schema[0].capitalize())
    return type(
        new_class_name,
        (PREMISElement,),
        {'defaults': property(defaults), 'schema': property(schema_getter)})


def data_find_all(data, path, dyn_cls=False):
    """Find and return all element-as-tuples in tuple ``data`` using simplified
    XPath ``path``.
    """
    path_parts = path.split('/')
    try:
        sub_elms = tuple(el for el in data if
                         isinstance(el, (tuple, list)) and
                         el[0] == path_parts[0])
    except IndexError:
        return None
    if len(path_parts) > 1:
        ret = []
        for sub_elm in sub_elms:
            for x in data_find_all(sub_elm, '/'.join(path_parts[1:])):
                ret.append(x)
        ret = tuple(ret)
    else:
        ret = sub_elms
    if ret and dyn_cls:
        cls = generate_element_class(ret[0])
        return tuple(cls(data=tuple_) for tuple_ in ret)
    return ret


def data_find_text(data, path):
    """Return the text value of the element-as-tuple in tuple ``data`` using
    simplified XPath ``path``.
    """
    el = data_find(data, path)
    if isinstance(el, (list, tuple)):
        texts = [child for child in el[1:]
                 if not isinstance(child, (tuple, list, dict))]
        if texts:
            return ' '.join([str(x) for x in texts])
    return None


def data_find_text_or_all(data, path, dyn_cls=False):
    text = data_find_text(data, path)
    if text:
        return text
    return data_find_all(data, path, dyn_cls=dyn_cls)


def get_event_type(data):
    return data_find_text(data, 'event_type')


def _get_event_detail_attr(attr, parsed_event_detail):
    try:
        return parsed_event_detail[attr]
    except KeyError:
        print('Unable to find attribute {} in event detail {}'.format(
            attr, parsed_event_detail))
        return 'No value found'


def _get_relationship_tag_names(premis_version):
    related_object_identifier = {'2.2': 'related_object_identification'}.get(
        premis_version, 'related_object_identifier')
    related_event_identifier = {'2.2': 'related_event_identification'}.get(
        premis_version, 'related_event_identifier')
    return related_object_identifier, related_event_identifier


def _generate_data(schema, elements, attributes=None, path=None):
    """Using tree-as-tuple ``schema`` as guide, return a tree-as-tuple ``data``
    representing a PREMIS XML element, where the values in dict ``elements`` and
    the values in dict ``attributes`` are located in the appropriate locations
    in the ``data`` tree structure.
    """
    path = path or []
    attributes = attributes or {}
    tag_name = schema[0]
    data = [tag_name]
    if attributes:
        data.append(attributes)
    new_path = path[:]
    new_path.append(tag_name)
    root = new_path[0]
    possible_paths = ['__'.join(new_path), tag_name]
    if root != tag_name and tag_name.startswith(root):
        possible_paths.append(tag_name.lstrip(root)[1:])
    for possible_path in possible_paths:
        val = elements.get(possible_path)
        if val:
            if isinstance(val, (tuple, list)):
                data = tuple(val)
            else:
                if attributes:
                    data = (tag_name, attributes, val)
                else:
                    data = (tag_name, val)
            return tuple(data)
    for subschema in schema[1:]:
        subel = _generate_data(subschema, elements, path=new_path)
        if (not subel) or (subel == subschema):
            continue
        if all(map(lambda x: isinstance(x, tuple), subel)):
            for subsubel in subel:
                data.append(subsubel)
        elif not el_is_empty(subel):
            data.append(subel)
    return tuple(data)


def el_is_empty(el):
    """Return ``True`` if tuple ``el`` represents an empty XML element."""
    if len(el) == 1 and not isinstance(el[0], (list, tuple)):
        return True
    subels_are_empty = []
    for subel in el:
        if isinstance(subel, (list, tuple)):
            subels_are_empty.append(el_is_empty(subel))
        else:
            subels_are_empty.append(not bool(subel))
    return all(subels_are_empty)


def get_attrs_to_paths(schema, attrs_to_paths=None, path=None):
    """Analyze PREMIS-element-as-tuple ``schema`` and return a dict that maps
    attribute names to the simplified XPaths needed to retrieve them, e.g.,::

        >>> {'object_identifier_type':
                'object_identifier/object_identifier_type',
             'object_identifier_value':
                'object_identifier/object_identifier_value'}
    """
    attrs_to_paths = attrs_to_paths or {}
    tag = schema[0]
    if len(schema) == 1:
        attrs_to_paths[tag] = '/'.join(path + [tag])
    else:
        for elem in schema[1:]:
            if isinstance(elem, dict):
                continue
            new_path = [] if path is None else path + [tag]
            if isinstance(elem, (list, tuple)):
                attrs_to_paths.update(
                    get_attrs_to_paths(elem, attrs_to_paths=attrs_to_paths, path=new_path))
            else:
                attrs_to_paths[tag] = '/'.join(new_path)
    return attrs_to_paths


def _get_xml_attribute_values(kwargs, premis_version=utils.PREMIS_VERSION):
    premis_el_attrs = utils.PREMIS_VERSIONS_MAP[premis_version]['meta'].copy()
    xsi_type = kwargs.get('xsi_type')
    if xsi_type:
        premis_el_attrs['xsi:type'] = xsi_type
    return premis_el_attrs


def _premis_version_from_data(data):
    """Given tuple ``data`` encoding a PREMIS element, attempt to return the
    PREMIS version it is using. If none can be found, return the default PREMIS
    version.
    """
    for child in data:
        if isinstance(child, dict):
            version = child.get('version')
            if version:
                return version
    return utils.PREMIS_VERSION
