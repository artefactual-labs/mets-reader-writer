Reading METS files
~~~~~~~~~~~~~~~~~~

metsrw supports reading METS files from disk, from strings, or from lxml_
`_Element` or `_ElementTree` objects.

.. testcode::

    # From a file on disk
    mets = metsrw.METSDocument.fromfile("../fixtures/complete_mets.xml")

    #  From bytes
    mets_str = b"""<?xml version='1.0' encoding='ASCII'?>
    <mets xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns="http://www.loc.gov/METS/" xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version18/mets.xsd">
        <metsHdr CREATEDATE="2015-12-16T22:38:48"/>
        <structMap ID="structMap_1" LABEL="Archivematica default" TYPE="physical"/>
    </mets>"""
    mets = metsrw.METSDocument.fromstring(mets_str)

    # From an lxml object
    tree = lxml.etree.parse("../fixtures/complete_mets.xml")
    mets = metsrw.METSDocument.fromtree(tree)


Accessing METS Data
-------------------

To retrieve an :class:`metsrw.FSEntry`, use the
:meth:`~metsrw.METSDocument.get_file` or
:meth:`~metsrw.METSDocument.all_files` methods.

.. doctest::

    >>> mets = metsrw.METSDocument()
    >>> file_uuid = str(uuid.uuid4())
    >>> file_1 = metsrw.FSEntry(
    ...     label="hello.pdf", path="test/hello.pdf", type="Item",
    ...     file_uuid=file_uuid)
    >>> mets.append_file(file_1)

    >>> mets.get_file(file_uuid=file_uuid)
    FSEntry(type='Item', path='test/hello.pdf', use='original', ...)

    >>> mets.all_files()
    {FSEntry(type='Item', path='test/hello.pdf', use='original', ...)}

    # Currently, filtering files can only be done via iteration
    >>> [entry for entry in mets.all_files() if entry.use == "original"]
    [FSEntry(type='Item', path='test/hello.pdf', use='original', ...)]


`amdSec` and `dmdSec` data is accessible via the
:attr:`~metsrw.FSEntry.amdsecs` and :attr:`~metsrw.FSEntry.dmdsecs`
properties.

.. doctest::

    >>> mets = metsrw.METSDocument.fromfile('../fixtures/complete_mets.xml')
    >>> fsentry = mets.get_file(file_uuid="ab5c67fc-8f80-4e46-9f20-8d5ae29c43f2")
    >>> amdsec1 = fsentry.amdsecs[0]
    >>> [section for section in amdsec1.subsections if section.subsection == 'techMD']
    [<metsrw.metadata.SubSection ...>]
    >>> fsentry.dmdsecs[0]
    <metsrw.metadata.SubSection ...>


.. note::
    In most cases, you'll want to access PREMIS data via the `get_premis`
    series of methods, rather than accessing the `amdSec` or `dmdSec` data
    directly. See `Accessing PREMIS Data`_ for more info.


Accessing PREMIS Data
---------------------

To access PREMIS_ metadata associated with a file, use the following
methods:

* :meth:`~metsrw.FSEntry.get_premis_objects`
* :meth:`~metsrw.FSEntry.get_premis_events`
* :meth:`~metsrw.FSEntry.get_premis_agents`
* :meth:`~metsrw.FSEntry.get_premis_rights`


.. doctest::

    # Currently, filtering PREMIS objects can only be done via iteration
    >>> ingestion_events = []
    >>> mets = metsrw.METSDocument.fromfile('../fixtures/complete_mets.xml')
    >>> for fsentry in mets.all_files():
    ...     for event in fsentry.get_premis_events():
    ...          if event.type == "ingestion":
    ...              ingestion_events.append(event)
    >>> ingestion_events[0]
    ('event', ...)


.. _lxml: https://lxml.de/index.html
.. _PREMIS: https://www.loc.gov/standards/premis/v3/index.html
