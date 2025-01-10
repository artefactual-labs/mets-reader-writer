# METS Reader & Writer

By [Artefactual](https://www.artefactual.com/)

[![PyPI version](https://badge.fury.io/py/metsrw.svg)](https://badge.fury.io/py/metsrw)
[![GitHub CI](https://github.com/artefactual-labs/mets-reader-writer/actions/workflows/test.yml/badge.svg)](https://github.com/artefactual-labs/mets-reader-writer/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/artefactual-labs/mets-reader-writer/branch/master/graph/badge.svg?token=1cXYbNlgJr)](https://codecov.io/gh/artefactual-labs/mets-reader-writer)

METSRW is a library to help with parsing and creating METS files.
It provides an API, and abstracts away the actual creation of the XML.
METSRW was initially created for use in [Archivematica](https://github.com/artefactual/archivematica/)
and is managed as part of that project.

You are free to copy, modify, and distribute metsrw with attribution under the
terms of the AGPL license. See the [LICENSE](LICENSE) file for details.

## Installation & Dependencies

METSRW can be installed with pip.

`pip install metsrw`

METSRW is tested with the all the [supported versions](https://devguide.python.org/versions/#supported-versions)
of Python.

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
