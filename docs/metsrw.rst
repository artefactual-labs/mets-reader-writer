metsrw
======


Basic Usage
-----------

Reading METS files
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Reads a file
    mets = metsrw.METSDocument.fromfile('path/to/file')

    # Parses a string
    mets = metsrw.METSDocument.fromstring("""<?xml version='1.0' encoding='ASCII'?>
    <mets xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns="http://www.loc.gov/METS/" xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version18/mets.xsd">
        <metsHdr CREATEDATE="2015-12-16T22:38:48"/>
        <structMap ID="structMap_1" LABEL="Archivematica default" TYPE="physical"/>
    </mets>""")

    # Parses an lxml.Element or lxml.ElementTree
    tree = lxml.etree.fromfile('path/to/file')
    mets = metsrw.METSDocument.fromtree(tree)


Writing METS files
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    mets = metsrw.METSDocument()
    file1 = metsrw.FSEntry("hello.pdf", file_uuid=str(uuid.uuid4()))
    mets.append_file(file1)

    mets.serialize()
    # <Element {http://www.loc.gov/METS/}mets at 0x104f89c88>

    mets.tostring()
    # b'<?xml version=\'1.0\' encoding=\'ASCII\'?>\n<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version111/mets.xsd">\n  <mets:metsHdr CREATEDATE="2019-03-26T23:16:08"/>\n  <mets:fileSec>\n    <mets:fileGrp USE="original">\n      <mets:file ID="file-ad6a74d1-f8c1-4a33-a2e4-469608e3331a" GROUPID="Group-ad6a74d1-f8c1-4a33-a2e4-469608e3331a">\n        <mets:FLocat xlink:href="hello.pdf" LOCTYPE="OTHER" OTHERLOCTYPE="SYSTEM"/>\n      </mets:file>\n    </mets:fileGrp>\n  </mets:fileSec>\n  <mets:structMap ID="structMap_1" LABEL="Archivematica default" TYPE="physical">\n    <mets:div TYPE="Item" LABEL="hello.pdf">\n      <mets:fptr FILEID="file-ad6a74d1-f8c1-4a33-a2e4-469608e3331a"/>\n    </mets:div>\n  </mets:structMap>\n  <mets:structMap ID="structMap_2" LABEL="Normative Directory Structure" TYPE="logical">\n    <mets:div TYPE="Item" LABEL="hello.pdf"/>\n  </mets:structMap>\n</mets:mets>\n'

    mets.write("/path/to/file")


API Documentation
-----------------

.. autoclass:: metsrw.METSDocument
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: metsrw.FSEntry
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: metsrw.metadata
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: metsrw.validate
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: metsrw.exceptions
    :members:
    :undoc-members:
    :show-inheritance:
