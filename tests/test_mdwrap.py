from lxml import etree
import pytest
from unittest import TestCase

import metsrw
from metsrw import utils


class TestMDWrap(TestCase):
    """ Test MDWrap class. """

    def test_fromfile(self):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse('fixtures/complete_mets.xml', parser=parser)

        mdwrap_el = root.find("mets:dmdSec[@ID='dmdSec_1']/" +
                              "mets:mdWrap", namespaces=utils.NAMESPACES)

        # Test properties
        mdwrap = metsrw.MDWrap.parse(mdwrap_el)
        assert mdwrap.data is not None
        assert mdwrap.data['title'] == 'Example DC title'
        assert mdwrap.data['creator'] == 'Example DC creator'
        assert mdwrap.data['subject'] == 'Example DC subject'
        assert mdwrap.data['description'] == 'Example DC description'
        assert mdwrap.data['publisher'] == 'Example DC publisher'
        assert mdwrap.data['contributor'] == 'Example DC contributor'
        assert mdwrap.data['date'] == '1984-01-01'
        assert mdwrap.data['format'] == 'Example DC format'
        assert mdwrap.data['identifier'] == 'Example DC identifier'
        assert mdwrap.data['source'] == 'Example DC source'
        assert mdwrap.data['relation'] == 'Example DC relation'
        assert mdwrap.data['language'] == 'en'
        assert mdwrap.data['coverage'] == 'Example DC coverage'
        assert mdwrap.data['rights'] == 'Example DC rights'

    def test_parse_wrong_element(self):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse('fixtures/complete_mets.xml', parser=parser)

        dmdsec_el = root.find("mets:dmdSec[@ID='dmdSec_1']", namespaces=utils.NAMESPACES)

        with pytest.raises(metsrw.ParseError):
            metsrw.MDWrap.parse(dmdsec_el)
