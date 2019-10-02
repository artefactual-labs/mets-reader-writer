[![PyPI version](https://badge.fury.io/py/metsrw.svg)](https://badge.fury.io/py/metsrw) [![Travis CI](https://travis-ci.org/artefactual-labs/mets-reader-writer.svg?branch=master)](https://travis-ci.org/artefactual-labs/mets-reader-writer) [![Coverage status](https://img.shields.io/coveralls/artefactual-labs/mets-reader-writer/master.svg)](https://coveralls.io/r/artefactual-labs/mets-reader-writer)

# METS Reader & Writer

By [Artefactual](https://www.artefactual.com/)

METSRW is a library to help with parsing and creating METS files.
It provides an API, and abstracts away the actual creation of the XML.
METSRW was initially created for use in [Archivematica](https://github.com/artefactual/archivematica/) and is managed as part of that project.

You are free to copy, modify, and distribute metsrw with attribution under the terms of the AGPL license.
See the [LICENSE](LICENSE) file for details.


## Installation & Dependencies

METSRW can be installed with pip.

`pip install metsrw`

METSRW has been tested with:

* Python 2.7
* Python 3.5
* Python 3.6
* Python 3.7

## Basic Usage

Read a METS file

    mets = metsrw.METSDocument.fromfile('path/to/file')  # Reads a file
    mets = metsrw.METSDocument.fromstring('<mets document>')  # Parses a string
    mets = metsrw.METSDocument.fromtree(lxml.ElementTree)  # Parses an lxml.Element or lxml.ElementTree

Create a new METS file

    mets = metsrw.METSDocument()


## Contributing

METSRW is in early development and welcomes feedback on the API and overall design!
Design goals, use cases, and a proposed API are in the [Github wiki](https://github.com/artefactual-labs/mets-reader-writer/wiki)
