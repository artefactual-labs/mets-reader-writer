import pytest

import metsrw


@pytest.mark.parametrize(
    "fixture_path",
    [
        "fixtures/mets_structmap_imported.xml",
        "fixtures/mets_structmap_arranged_sip.xml",
    ],
    ids=["mets_with_structmap_imported_from_xml", "mets_from_arranged_sip"],
)
def test_custom_struct_maps_are_serialized(fixture_path):
    """
    Logical structMaps other than the normative one should be parsed and
    serialized correctly.
    """
    mets = metsrw.METSDocument.fromfile(fixture_path)
    assert len(mets._custom_structmaps) == 1

    result = mets.serialize()
    custom_struct_maps = [
        e
        for e in result.findall(
            'mets:structMap[@TYPE="logical"]',
            namespaces=metsrw.NAMESPACES,
        )
        if e.attrib.get("LABEL") != "Normative Directory Structure"
    ]
    assert len(custom_struct_maps) == 1
