Reading METS files
~~~~~~~~~~~~~~~~~~

metsrw supports reading METS files from disk, from strings, or from lxml_
`_Element` or `_ElementTree` objects.

.. code-block:: python

    # From a file on disk
    mets = metsrw.METSDocument.fromfile('path/to/file')

    #  From a string
    mets_str = """<?xml version='1.0' encoding='ASCII'?>
    <mets xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns="http://www.loc.gov/METS/" xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version18/mets.xsd">
        <metsHdr CREATEDATE="2015-12-16T22:38:48"/>
        <structMap ID="structMap_1" LABEL="Archivematica default" TYPE="physical"/>
    </mets>"""
    mets = metsrw.METSDocument.fromstring(mets_str)

    # From an lxml object
    tree = lxml.etree.fromfile('path/to/file')
    mets = metsrw.METSDocument.fromtree(tree)


Accessing METS Data
-------------------

To retrieve an :class:`metsrw.FSEntry`, use the
:func:`~metsrw.METSDocument.get_file` method.

.. code-block:: python

    mets = metsrw.METSDocument()
    file_uuid = str(uuid.uuid4())
    file_1 = metsrw.FSEntry(
        label="hello.pdf", path="test/hello.pdf", type="Item",
        file_uuid=file_uuid)
    mets.append_file(file_1)

    # Returns file_1
    mets.get_file(file_uuid=file_uuid)


.. _lxml: https://lxml.de/index.html
