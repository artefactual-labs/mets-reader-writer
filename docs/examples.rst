Example usage
=============

Parsing METS documents
----------------------

Example of listing the relative file paths of preservation files referenced in
a METS file:::

  import metsrw

  mets = metsrw.METSDocument.fromfile('fixtures/complete_mets_2.xml')
  for entry in mets.all_files():
      if entry.use == 'preservation':
          print entry.path

Example of retrieving a file by UUID:::

  import metsrw

  mets = metsrw.METSDocument.fromfile('fixtures/complete_mets_2.xml')
  entry = mets.get_file('46b7cb96-792c-4441-a5d6-67c83313501c')
  print entry.path

Creating/modifying METS documents
---------------------------------

Example creation of a METS document (without PREMIS or Dublin Core metadata):::

  import metsrw
  import uuid

  mw = metsrw.METSDocument()

  # Create object entries
  file1 = metsrw.FSEntry('objects/cat.png', file_uuid=str(uuid.uuid4()))
  file2 = metsrw.FSEntry('objects/dog.jpg', file_uuid=str(uuid.uuid4()))

  # Create preservation derivative entries
  file1p = metsrw.FSEntry('objects/cat-preservation.tiff', use='preservation', file_uuid=str(uuid.uuid4()), derived_from=file1)
  file2p = metsrw.FSEntry('objects/dog-preservation.tiff', use='preservation', file_uuid=str(uuid.uuid4()), derived_from=file2)

  # Create object directory entry
  objects = metsrw.FSEntry('objects', type='Directory', children=[file1, file2, file1p, file2p])

  # Create metadata subdirectories then metadata directory entry
  children = [
      metsrw.FSEntry('transfers', type='Directory', children=[]),
      metsrw.FSEntry('metadata/metadata.csv', use='metadata', file_uuid=str(uuid.uuid4())),
  ]
  metadata = metsrw.FSEntry('metadata', type='Directory', children=children)

  # Create submission METS entry and submission documentation parent directory entry
  children = [
      metsrw.FSEntry('submissionDocumentation/METS.xml', use='submissionDocumentation', file_uuid=str(uuid.uuid4())),
  ]
  sub_doc = metsrw.FSEntry('submissionDocumentation', type='Directory', children=children)

  # Create SIP entry containing objects, metadata, and submission documentaton entries
  children = [objects, metadata, sub_doc]
  sip = metsrw.FSEntry('sipname-uuid', type='Directory', children=children)

  # Add SIP entry to METS document and write to file
  mw.append_file(sip)
  mw.write('mets.xml', fully_qualified=True, pretty_print=True)
