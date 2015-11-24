METS Reader & Writer
====================

METSRW is a library to help with parsing and creating METS files.
It provides an API, and abstracts away the actual creation of the XML.

Installation:

  python setup.py install

Once installed, the REST server can be started using:

  mets_server

The REST server will run on port 8000. Here is an example use of curl to parse
a METS XML file and populate a JSON file:

  curl -v -d "@mets.xml" http://127.0.0.1:8000/api/mets -o mets.json  
