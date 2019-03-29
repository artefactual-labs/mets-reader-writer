Writing METS Files
------------------

Building METS Documents
~~~~~~~~~~~~~~~~~~~~~~~

To add data to a :class:`metsrw.METSDocument`, create and append
:class:`metsrw.FSEntry` objects.


.. code-block:: python

    mets = metsrw.METSDocument()
    directory_1 = metsrw.FSEntry(label="test", path="test", type="Directory")

    file_1 = metsrw.FSEntry(
        label="hello.pdf", path="test/hello.pdf", type="Item",
        file_uuid=str(uuid.uuid4()))
    directory_1.children.append(file_1)

    file_2 = metsrw.FSEntry(
        label="demo.jpg", path="test/demo.jpg", type="Item",
        file_uuid=str(uuid.uuid4()))
    directory_1.children.append(file_2)

    mets.append_file(file1)


Adding metadata is done via the :class:`metsrw.FSEntry`.

.. code-block:: python

    file_1 = metsrw.FSEntry(
        label="hello.pdf", path="test/hello.pdf", type="Item",
        file_uuid=str(uuid.uuid4()))

    file1.add_premis_object("<premis>object</premis>")
    file1.add_premis_event("<premis>event</premis>")
    file1.add_premis_agent("<premis>agent</premis>")
    rights = file1.add_premis_rights("<premis>rights</premis>")
    dc = file1.add_dublin_core("<dublincore>metadata</dublincore>")

    # Replaces added metatdata
    rights.replace_with(file1.add_premis_rights("<premis>newer rights</premis>"))


Serialization
~~~~~~~~~~~~~

metsrw supports serialization to file, bytes or lxml_ Element object.


.. code-block:: python

    >>> mets = metsrw.METSDocument()
    >>> file1 = metsrw.FSEntry("hello.pdf", file_uuid=str(uuid.uuid4()))
    >>> mets.append_file(file1)

    >>> # To file on disk
    >>> mets.write("/path/to/file")

    >>> # To _Element object
    >>> mets.serialize()
    <Element {http://www.loc.gov/METS/}mets at 0x104f89c88>

    >>> # To bytes
    >>> mets.tostring()
    b'<?xml version=\'1.0\' encoding=\'ASCII\'?>\n<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version111/mets.xsd">\n  <mets:metsHdr CREATEDATE="2019-03-26T23:16:08"/>\n  <mets:fileSec>\n    <mets:fileGrp USE="original">\n      <mets:file ID="file-ad6a74d1-f8c1-4a33-a2e4-469608e3331a" GROUPID="Group-ad6a74d1-f8c1-4a33-a2e4-469608e3331a">\n        <mets:FLocat xlink:href="hello.pdf" LOCTYPE="OTHER" OTHERLOCTYPE="SYSTEM"/>\n      </mets:file>\n    </mets:fileGrp>\n  </mets:fileSec>\n  <mets:structMap ID="structMap_1" LABEL="Archivematica default" TYPE="physical">\n    <mets:div TYPE="Item" LABEL="hello.pdf">\n      <mets:fptr FILEID="file-ad6a74d1-f8c1-4a33-a2e4-469608e3331a"/>\n    </mets:div>\n  </mets:structMap>\n  <mets:structMap ID="structMap_2" LABEL="Normative Directory Structure" TYPE="logical">\n    <mets:div TYPE="Item" LABEL="hello.pdf"/>\n  </mets:structMap>\n</mets:mets>\n'


.. _lxml: https://lxml.de/index.html
