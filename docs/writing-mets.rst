Writing METS Files
------------------

Building METS Documents
~~~~~~~~~~~~~~~~~~~~~~~

To add data to a :class:`metsrw.METSDocument`, create and append
:class:`metsrw.FSEntry` objects.


.. doctest::

    >>> mets = metsrw.METSDocument()
    >>> directory_1 = metsrw.FSEntry(label="test", path="test", type="Directory")
    >>> file_1 = metsrw.FSEntry(
    ...     label="hello.pdf", path="test/hello.pdf", type="Item",
    ...     file_uuid=str(uuid.uuid4()))
    >>> directory_1.children.append(file_1)
    >>> file_2 = metsrw.FSEntry(
    ...    label="demo.jpg", path="test/demo.jpg", type="Item",
    ...    file_uuid=str(uuid.uuid4()))
    >>> directory_1.children.append(file_2)
    >>> mets.append_file(directory_1)
    >>> mets.all_files()
    {FSEntry(...), FSEntry(...)}


Adding metadata is done via the :class:`metsrw.FSEntry`.

.. testcode::

    file_1 = metsrw.FSEntry(
        label="hello.pdf", path="test/hello.pdf", type="Item",
        file_uuid=str(uuid.uuid4()))

    file_1.add_premis_object("<premis>object</premis>")
    file_1.add_premis_event("<premis>event</premis>")
    file_1.add_premis_agent("<premis>agent</premis>")
    rights = file_1.add_premis_rights("<premis>rights</premis>")
    dc = file_1.add_dublin_core("<dublincore>metadata</dublincore>")

    # Replaces added metadata
    rights.replace_with(file_1.add_premis_rights("<premis>newer rights</premis>"))


Serialization
~~~~~~~~~~~~~

metsrw supports serialization to file, bytes or lxml_ Element object.


.. testsetup:: serialization

    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, "demo.xml")
    mets = metsrw.METSDocument()
    file1 = metsrw.FSEntry("hello.pdf", file_uuid=str(uuid.uuid4()))
    mets.append_file(file1)

.. testcleanup:: serialization

    os.remove(output_path)
    os.removedirs(temp_dir)

.. doctest:: serialization

    >>> mets = metsrw.METSDocument()
    >>> file1 = metsrw.FSEntry("hello.pdf", file_uuid=str(uuid.uuid4()))
    >>> mets.append_file(file1)

    # To file on disk
    >>> mets.write(output_path)

    # To _Element object
    >>> mets.serialize()
    <Element {http://www.loc.gov/METS/}mets ...>

    # To bytes
    >>> mets.tostring()
    b'<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<mets:mets ...'


.. _lxml: https://lxml.de/index.html
