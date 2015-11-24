METS Reader & Writer
====================

METSRW is a library to help with parsing and creating METS files.
It provides an API, and abstracts away the actual creation of the XML.

Installation:

  python setup.py install

Once installed, the REST server can be started using:

  mets_server

The REST server will, by default, run on port 8001. You can optionally specify
a different port using the `-p` flag. For example:

  mets_server -p 8080

Here is an example use of curl to request the REST server parse a METS XML
file and populate a JSON file with the results:

  curl -v -d "@mets.xml" http://127.0.0.1:8001/api/mets -o mets.json 

Here is some example JSON output ("..." indicates content that has been removed
for brevity:

  {
    "response": {
      "date": "2016-04-08T01:56:29",
      "files": [
        {
          "checksum": null,
          "checksumtype": null,
          "children": [],
          "derived_from": null,
          "file_uuid": "42ce424d-2c04-4f40-9cf2-ed234a44f2d5",
          "label": "METS.xml",
          "path": "objects/submissionDocumentation/transfer-A_Test-9d6d5235-e8cd-4b51-96a5-93bb3d1b6aa5/METS.xml",
          "type": "Item",
          "use": "submissionDocumentation"
        },
        {
          "checksum": null,
          "checksumtype": null,
          "children": [],
          "derived_from": null,
          "file_uuid": "776c90eb-2293-4672-a040-7c1547b9305b",
          "label": "Nemastylis_geminiflora_Flower.PNG",
          "path": "objects/Nemastylis_geminiflora_Flower.PNG",
          "type": "Item",
          "use": "original"
        }
      ],
      "mdsecs": [
        {
          "id": "amdSec_2",
          "subsections": [
            {
              "created": null,
              "id": "techMD_2",
              "newer": null,
              "older": null,
              "status": null,
              "subsection": "techMD"
            },
            ...
          ]
        },
        {
          "id": "amdSec_1",
          "subsections": [
            {
              "created": null,
              "id": "techMD_1",
              "newer": null,
              "older": null,
              "status": null,
              "subsection": "techMD"
            },
            ...
          ]
        }
      ]
    }
  }
