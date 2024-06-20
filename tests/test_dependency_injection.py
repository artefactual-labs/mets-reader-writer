from unittest import TestCase

import metsrw
import metsrw.plugins.premisrw as premisrw

from .constants import EX_AGT_1
from .constants import EX_AGT_2
from .constants import EX_COMPR_EVT
from .constants import EX_PTR_AIP_SUBTYPE
from .constants import EX_PTR_DATE_CREATED_BY_APPLICATION
from .constants import EX_PTR_FORMAT_NAME
from .constants import EX_PTR_FORMAT_REGISTRY_KEY
from .constants import EX_PTR_IDENTIFIER_VALUE
from .constants import EX_PTR_MESSAGE_DIGEST
from .constants import EX_PTR_MESSAGE_DIGEST_ALGORITHM
from .constants import EX_PTR_PACKAGE_TYPE
from .constants import EX_PTR_PATH
from .constants import EX_PTR_SIZE
from .constants import EX_PTR_XSI_TYPE


class BetterPREMISObject:
    """A dummy PREMIS object class that can be used to meet the dependency of
    ``FSEntry``.
    """

    def __init__(self, tree):
        self.tree = tree

    @classmethod
    def fromtree(cls, tree):
        return cls(tree)

    def serialize(self):
        return self.tree


class TestDependencyInjection(TestCase):
    """Test dependency injection of metadata functionality into the
    FSEntry class.
    """

    def test_assertion_creators(self):
        """Tests that the assertion creators ``has_methods`` and
        ``has_class_methods`` behave correctly.

        Note the false positives below. In python 3 it is easy to distinguish
        regular methods from class methods in a class but to do it in a 2/3
        compatible way seems like too much introspection bother right now. The
        more difficult issue would seem to be distinguishing regular methods
        from static methods on a class. However, these are acceptable flaws if
        we are mainly concerned with asserting the existence of a) specific
        class methods on classes and b) specific methods (of any type) on
        classes.
        """

        class C:
            @classmethod
            def cm(cls):
                pass

            @staticmethod
            def sm():
                pass

            def rm(self):
                pass

        c = C()

        class X:
            pass

        x = X()

        has_rm_method = metsrw.has_methods("rm")
        has_cm_method = metsrw.has_methods("cm")
        has_sm_method = metsrw.has_methods("sm")
        has_xm_method = metsrw.has_methods("xm")

        has_rm_class_method = metsrw.has_class_methods("rm")
        has_cm_class_method = metsrw.has_class_methods("cm")
        has_sm_class_method = metsrw.has_class_methods("sm")
        has_xm_class_method = metsrw.has_class_methods("xm")

        # C should have classmethod 'cm' and regular method 'rm'
        assert has_rm_method(C) is True
        assert has_cm_method(C) is True  # false positive
        assert has_sm_method(C) is True  # false positive
        assert has_xm_method(C) is False
        assert has_rm_class_method(C) is False
        assert has_cm_class_method(C) is True
        assert has_sm_class_method(C) is False
        assert has_xm_class_method(C) is False

        # c should have classmethod 'cm' and regular method 'rm'
        assert has_rm_method(c) is True
        assert has_cm_method(c) is False
        assert has_sm_method(c) is False
        assert has_xm_method(c) is False
        assert has_rm_class_method(c) is False
        assert has_cm_class_method(c) is True
        assert has_sm_class_method(c) is False
        assert has_xm_class_method(c) is False

        # X should have nothing
        assert has_rm_method(X) is False
        assert has_cm_method(X) is False
        assert has_sm_method(X) is False
        assert has_xm_method(X) is False
        assert has_rm_class_method(X) is False
        assert has_cm_class_method(X) is False
        assert has_sm_class_method(X) is False
        assert has_xm_class_method(X) is False

        # x should have nothing
        assert has_rm_method(x) is False
        assert has_cm_method(x) is False
        assert has_sm_method(x) is False
        assert has_xm_method(x) is False
        assert has_rm_class_method(x) is False
        assert has_cm_class_method(x) is False
        assert has_sm_class_method(x) is False
        assert has_xm_class_method(x) is False

    def test_dependency_injection(self):
        """Test the dependency injection (DI) infrastructure for metsrw plugins.

        - client: metsrw.FSEntry
        - services: classes for reading and writing metadata elements, e.g.,
          the PREMISObject class of metsrw.plugins.premisrw or other classes
          exposing the same interface.
        - injector: this test code or the code in metsrw/di.py which calls
          ``provide`` on the ``feature_broker`` singleton.

        The ``FSEntry`` class declares its dependency on the class attributes
        ``premis_object_class``, ``premis_event_class``, and
        ``premis_agent_class`` and further requires that these return classes
        with ``fromtree`` and ``serialize`` methods::

            >>> premis_object_class = Dependency(
            ...     has_methods('serialize'),
            ...     has_class_methods('fromtree'),
            ...     is_class)

        """

        # Clear the feature broker and then register/provide the premisrw
        # plugin classes (services) with the feature broker.
        feature_broker = metsrw.feature_broker
        assert len(feature_broker) == 4
        feature_broker.clear()
        assert not feature_broker
        feature_broker.provide("premis_object_class", premisrw.PREMISObject)
        feature_broker.provide("premis_event_class", premisrw.PREMISEvent)
        feature_broker.provide("premis_agent_class", premisrw.PREMISAgent)
        feature_broker.provide("premis_rights_class", premisrw.PREMISRights)
        assert len(feature_broker) == 4

        # Create premisrw instances.
        compression_premis_event = premisrw.PREMISEvent(data=EX_COMPR_EVT)
        premis_events = [compression_premis_event]
        premis_agents = [premisrw.PREMISAgent(data=x) for x in [EX_AGT_1, EX_AGT_2]]
        (
            _,
            compression_program_version,
            archive_tool,
        ) = compression_premis_event.compression_details
        premis_object = premisrw.PREMISObject(
            xsi_type=EX_PTR_XSI_TYPE,
            identifier_value=EX_PTR_IDENTIFIER_VALUE,
            message_digest_algorithm=EX_PTR_MESSAGE_DIGEST_ALGORITHM,
            message_digest=EX_PTR_MESSAGE_DIGEST,
            size=EX_PTR_SIZE,
            format_name=EX_PTR_FORMAT_NAME,
            format_registry_key=EX_PTR_FORMAT_REGISTRY_KEY,
            creating_application_name=archive_tool,
            creating_application_version=compression_program_version,
            date_created_by_application=EX_PTR_DATE_CREATED_BY_APPLICATION,
        )
        transform_files = compression_premis_event.get_decompression_transform_files()

        # Create metsrw ``METSDocument`` and ``FSEntry`` instances.
        mets_doc = metsrw.METSDocument()
        fs_entry = metsrw.FSEntry(
            path=EX_PTR_PATH,
            file_uuid=EX_PTR_IDENTIFIER_VALUE,
            use=EX_PTR_PACKAGE_TYPE,
            type=EX_PTR_PACKAGE_TYPE,
            transform_files=transform_files,
            mets_div_type=EX_PTR_AIP_SUBTYPE,
        )
        mets_doc.append_file(fs_entry)

        # Use the ``add_premis_...`` methods to add the PREMIS metadata
        # elements to the ``FSEntry`` instance. This will assert that each
        # PREMIS instance is of the correct type (e.g., that ``premis_object``
        # is an instance of ``FSEntry().premis_object_class``) and will call the
        # instance's ``serialize`` method and incorporate the resulting
        # ``lxml.etree._ElementTree`` instance into the ``FSEntry`` instance
        # appropriately.
        fs_entry.add_premis_object(premis_object)
        for premis_event in premis_events:
            fs_entry.add_premis_event(premis_event)
        for premis_agent in premis_agents:
            fs_entry.add_premis_agent(premis_agent)

        # Assert that the instances returned by the
        # ``FSEntry().get_premis_...`` methods are of the anticipated type.
        new_premis_agents = fs_entry.get_premis_agents()
        for new_premis_agent in new_premis_agents:
            assert isinstance(new_premis_agent, premisrw.PREMISAgent)
            assert new_premis_agent in premis_agents
            assert id(new_premis_agent) not in [id(pa) for pa in premis_agents]
        new_premis_events = fs_entry.get_premis_events()
        for new_premis_event in new_premis_events:
            assert isinstance(new_premis_event, premisrw.PREMISEvent)
            assert new_premis_event in premis_events
            assert id(new_premis_event) not in [id(pa) for pa in premis_events]
        new_premis_objects = fs_entry.get_premis_objects()
        for new_premis_object in new_premis_objects:
            assert isinstance(new_premis_object, premisrw.PREMISObject)
            assert new_premis_object == premis_object
            assert id(new_premis_object) is not premis_object

        # Assert that the resulting mets XML contains a
        # premis:objectIdentifierValue in the anticipated location in the
        # structure with the anticipated value.
        mets_doc_el = mets_doc.serialize()
        xpath = (
            'mets:amdSec/mets:techMD/mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]'
            "/mets:xmlData/premis:object/premis:objectIdentifier/"
            "premis:objectIdentifierValue"
        )
        a = mets_doc_el.find(xpath, namespaces=metsrw.NAMESPACES)
        assert a.text == EX_PTR_IDENTIFIER_VALUE

        # Now change the feature broker so that ``FSEntry``'s dependency on a
        # ``premis_object_class`` class attribute is being fulfilled by a new
        # class: ``BetterPREMISObject``.
        feature_broker.provide("premis_object_class", BetterPREMISObject)

        # Now create a new PREMIS object
        premis_object_tree = premis_object.serialize()
        better_premis_object = BetterPREMISObject.fromtree(premis_object_tree)

        # And re-create the ``METSDocument`` and ``FSEntry`` instances.
        mets_doc = metsrw.METSDocument()
        fs_entry = metsrw.FSEntry(
            path=EX_PTR_PATH,
            file_uuid=EX_PTR_IDENTIFIER_VALUE,
            use=EX_PTR_PACKAGE_TYPE,
            type=EX_PTR_PACKAGE_TYPE,
            transform_files=transform_files,
            mets_div_type=EX_PTR_AIP_SUBTYPE,
        )
        mets_doc.append_file(fs_entry)

        # Add the PREMIS metadata again, but this time use the instance of
        # ``BetterPREMISObject``.
        fs_entry.add_premis_object(better_premis_object)
        for premis_event in premis_events:
            fs_entry.add_premis_event(premis_event)
        for premis_agent in premis_agents:
            fs_entry.add_premis_agent(premis_agent)

        # Assert that the instances returned by the
        # ``FSEntry().get_premis_...`` methods are of the anticipated type.
        new_premis_objects = fs_entry.get_premis_objects()
        for new_premis_object in new_premis_objects:
            assert isinstance(new_premis_object, BetterPREMISObject)

        # Make sure we can still find the PREMIS object id value.
        mets_doc_el = mets_doc.serialize()
        assert (
            mets_doc_el.find(xpath, namespaces=metsrw.NAMESPACES).text
            == EX_PTR_IDENTIFIER_VALUE
        )

        # Reset the feature broker to its default state so subsequent tests
        # don't break.
        metsrw.set_feature_broker_to_default_state(feature_broker)
