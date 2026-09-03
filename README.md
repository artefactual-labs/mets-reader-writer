# METS Reader & Writer

By [Artefactual](https://www.artefactual.com/)

[![PyPI version](https://badge.fury.io/py/metsrw.svg)](https://badge.fury.io/py/metsrw)
[![GitHub CI](https://github.com/artefactual-labs/mets-reader-writer/actions/workflows/test.yml/badge.svg)](https://github.com/artefactual-labs/mets-reader-writer/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/artefactual-labs/mets-reader-writer/branch/main/graph/badge.svg?token=1cXYbNlgJr)](https://codecov.io/gh/artefactual-labs/mets-reader-writer)

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

## Development workflows

Install uv using the [uv installation documentation], then synchronize the
locked project and development dependencies:

    make sync

The Makefile exposes the common workflows:

- `make sync-runtime` installs only the project and runtime dependencies.
- `make sync` also installs development tools.
- `make lock-check` verifies that `uv.lock` matches `pyproject.toml`.
- `make lock` refreshes the lock without upgrading existing versions, while
  `make upgrade` upgrades all dependencies.
- `make check` verifies the lock and runs all pre-commit checks.
- `make test PYTEST_ARGS="..."` runs pytest with optional arguments. Run it
  from the repository root because the tests open `fixtures/` paths relative
  to the current directory.
- `make docs` runs the documentation doctests and checks that the
  documentation builds without warnings; `make docs-html` writes the HTML
  pages to `docs/_build/html`.
- `make package-check` builds the sdist and wheel into `dist/` and validates
  them with twine.

Declare runtime dependencies in `project.dependencies` and development
dependencies in `dependency-groups` in `pyproject.toml`: the `docs` group
holds the Sphinx dependencies used by Read the Docs and the `dev` group
includes it. The committed `uv.lock` is the sole dependency lock; requirements
exports are not maintained.

The exact default interpreter is pinned in `.python-version`. Local uv
commands and the `setup-uv` GitHub Action discover it automatically. The CI
test matrix and Read the Docs override this default to exercise other
supported Python versions. To upgrade the default, update `.python-version`
and run `make lock`. If the supported range changes, also update
`project.requires-python`, the classifiers and the CI matrix.

`tool.uv.required-version` declares the minimum supported uv version and
accepts newer global installations. To raise it, update the value and run
`make lock` and `make check`.

The package version lives in `metsrw/__init__.py`; release commits only need
to update `__version__` there. The lock does not record the project version.

[uv installation documentation]: https://docs.astral.sh/uv/getting-started/installation/

## Contributing

METSRW is in early development and welcomes feedback on the API and overall design!
Design goals, use cases, and a proposed API are in the [Github wiki](https://github.com/artefactual-labs/mets-reader-writer/wiki)
