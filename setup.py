"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='metsrw',
    version='0.1.0',

    description='Library for dealing with METS files.',
    long_description=long_description,

    url='https://github.com/artefactual-labs/mets-reader-writer/',

    author='Artefactual',
    author_email='info@artefactual.com',

    license='AGPL',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],

    keywords='mets',

    packages=find_packages(exclude=['docs', 'fixtures', 'requirements', 'tests*']),

    install_requires=['lxml', 'six'],
)
