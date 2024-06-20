"""Tests that metsrw can create normative logical structMaps correctly.

A normative logical structMap is a <mets:structMap> with TYPE="logical" and
LABEL="Normative Directory Structure", which documents empty directories that
are absent in the standard physical structural map.

"""

import uuid
from unittest import TestCase

from lxml import etree

import metsrw
from metsrw.plugins.premisrw import PREMIS_3_0_NAMESPACES
from metsrw.plugins.premisrw import PREMISObject
from metsrw.plugins.premisrw import lxmlns


class TestNormativeStructMap(TestCase):
    """Test normative logical structmap class."""

    def test_read_normative_structmaps(self):
        """It should be able to read a normative logical structural map.

        When parsing a mets file that contains a logical structmap with label
        "Normative Directory Structure", metsrw should find the empty
        directories in that logical structmap and create ``FSEntry`` instances
        for them. During (re-)serialization, the physical structmap should not
        document the empty directory but the normative (logical) one should.
        """
        mw = metsrw.METSDocument.fromfile("fixtures/mets_empty_dirs.xml")
        empty_dir_filesec = mw.get_file(label="dir2aiii", type="Directory")
        assert empty_dir_filesec is not None

        structmap = mw._structmap()
        normative_structmap = mw._normative_structmap()
        exists_only_in_normative = (
            'mets:div[@LABEL="thu1-31d2689d-91d0-42b4-91be-1b1b0c2e65a4"]/'
            'mets:div[@LABEL="objects"]/'
            'mets:div[@LABEL="dir2"]/'
            'mets:div[@LABEL="dir2a"]/'
            'mets:div[@LABEL="dir2aiii"]'
        )
        exists_in_both = (
            'mets:div[@LABEL="thu1-31d2689d-91d0-42b4-91be-1b1b0c2e65a4"]/'
            'mets:div[@LABEL="objects"]/'
            'mets:div[@LABEL="dir2"]/'
            'mets:div[@LABEL="dir2a"]/'
            'mets:div[@LABEL="dir2aii"]'
        )
        assert structmap.find(exists_only_in_normative, metsrw.NAMESPACES) is None
        assert structmap.find(exists_in_both, metsrw.NAMESPACES) is not None
        assert (
            normative_structmap.find(exists_only_in_normative, metsrw.NAMESPACES)
            is not None
        )
        assert normative_structmap.find(exists_in_both, metsrw.NAMESPACES) is not None

    def test_write_normative_structmap(self):
        """It should be able to write a normative logical structural map."""

        # Create the empty directory as an FSEntry and give it a simple PREMIS
        # object.
        d_empty = metsrw.FSEntry("EMPTY_DIR", type="Directory")
        d_empty_id = str(uuid.uuid4())
        d_empty_premis_object = PREMISObject(
            identifier_value=d_empty_id,
            premis_version="3.0",
            xsi_type="premis:intellectualEntity",
        )
        d_empty.add_premis_object(d_empty_premis_object)

        # Create the parent directory of the empty directory and give it a
        # simple PREMIS object also.
        f3 = metsrw.FSEntry("level3.txt", file_uuid=str(uuid.uuid4()))
        f3.add_dmdsec(etree.Element("data"), "OTHER")
        d2 = metsrw.FSEntry("dir2", type="Directory", children=[f3, d_empty])
        d2_id = str(uuid.uuid4())
        d2_premis_object = PREMISObject(identifier_value=d2_id)
        d2.add_premis_object(d2_premis_object)

        # Create more directories and files and add the root of the dir
        # structure to a metsrw METSDocument instance.
        f2 = metsrw.FSEntry("level2.txt", file_uuid=str(uuid.uuid4()))
        d1 = metsrw.FSEntry("dir1", type="Directory", children=[d2, f2])
        f1 = metsrw.FSEntry("level1.txt", file_uuid=str(uuid.uuid4()))
        d = metsrw.FSEntry("root", type="Directory", children=[d1, f1])
        mw = metsrw.METSDocument()
        mw.append_file(d)

        # Expect to find all of our files and directories in the return value
        # of ``all_files``, including the empty directory.
        files = mw.all_files()
        assert files
        assert len(files) == 7
        assert d in files
        assert f1 in files
        assert d1 in files
        assert f2 in files
        assert d2 in files
        assert f3 in files
        assert d_empty in files

        # Get XPaths for the empty directory and its sister file. The file
        # should exist in both structmaps, the empty directory should only
        # exist in the normative logical structmap.
        exists_in_both_path = (
            'mets:div[@LABEL="root"]/'
            'mets:div[@LABEL="dir1"]/'
            'mets:div[@LABEL="dir2"]/'
            'mets:div[@LABEL="level3.txt"]'
        )
        exists_in_normative_only_path = (
            'mets:div[@LABEL="root"]/'
            'mets:div[@LABEL="dir1"]/'
            'mets:div[@LABEL="dir2"]/'
            'mets:div[@LABEL="EMPTY_DIR"]'
        )

        # Expect that the empty directory is not in the physical structmap.
        structmap_el = mw._structmap()
        assert structmap_el.find(exists_in_both_path, metsrw.NAMESPACES) is not None
        assert (
            structmap_el.find(exists_in_normative_only_path, metsrw.NAMESPACES) is None
        )

        # Expect that the empty directory is in the normative logical structmap.
        normative_structmap_el = mw._normative_structmap()
        assert (
            normative_structmap_el.find(exists_in_both_path, metsrw.NAMESPACES)
            is not None
        )
        empty_div_el = normative_structmap_el.find(
            exists_in_normative_only_path, metsrw.NAMESPACES
        )
        assert empty_div_el is not None

        # Expect that the empty directory in the normative logical structmap
        # has a DMDID that references a dmdSec in the METS document and that
        # this dmdSec contains a PREMIS object.
        dmdid = empty_div_el.get("DMDID")
        assert dmdid.startswith("dmdSec_")
        doc = mw.serialize()
        empty_dir_dmd_sec = doc.find(f'mets:dmdSec[@ID="{dmdid}"]', metsrw.NAMESPACES)
        assert empty_dir_dmd_sec is not None
        xml_data_el = empty_dir_dmd_sec.find(
            "mets:mdWrap/mets:xmlData", metsrw.NAMESPACES
        )
        premis_object_el_retrieved = xml_data_el.find(
            "premis:object", PREMIS_3_0_NAMESPACES
        )
        d_empty_id_retrieved = premis_object_el_retrieved.find(
            "premis:objectIdentifier/premis:objectIdentifierValue",
            PREMIS_3_0_NAMESPACES,
        ).text
        assert d_empty_id_retrieved == d_empty_id
        xsi_type = premis_object_el_retrieved.get(
            "{}type".format(lxmlns("xsi", premis_version="3.0"))
        )
        assert xsi_type == "premis:intellectualEntity"

        # Expect that the file in the normative logical structmap includes the
        # DMDID attribute.
        dmdid = normative_structmap_el.find(exists_in_both_path, metsrw.NAMESPACES).get(
            "DMDID"
        )
        assert dmdid.startswith("dmdSec_")
        file_3_dmd_sec = doc.find(f'mets:dmdSec[@ID="{dmdid}"]', metsrw.NAMESPACES)
        assert file_3_dmd_sec is not None
