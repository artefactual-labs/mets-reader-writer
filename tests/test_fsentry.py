import pytest
from unittest import TestCase
import uuid

import metsrw


class TestFSEntry(TestCase):
    """ Test FSEntry class. """

    def test_file_id(self):
        d = metsrw.FSEntry('dir', type='Directory')
        assert d.file_id() is None
        f = metsrw.FSEntry('level1.txt')
        with pytest.raises(metsrw.MetsError):
            f.file_id()
        file_uuid = str(uuid.uuid4())
        f = metsrw.FSEntry('level1.txt', file_uuid=file_uuid)
        assert f.file_id() == 'file-' + file_uuid

    def test_group_id(self):
        f = metsrw.FSEntry('level1.txt')
        assert f.group_id() is None
        file_uuid = str(uuid.uuid4())
        f = metsrw.FSEntry('level1.txt', file_uuid=file_uuid)
        assert f.group_id() == 'Group-' + file_uuid
        derived = metsrw.FSEntry('level3.txt', file_uuid=str(uuid.uuid4()), derived_from=f)
        assert derived.group_id() == 'Group-' + file_uuid
        assert derived.group_id() == f.group_id()

    def test_add_metadata_to_fsentry(self):
        f1 = metsrw.FSEntry('file1.txt', file_uuid=str(uuid.uuid4()))
        f1.add_dublin_core('<dc />')
        assert f1.dmdsecs
        assert len(f1.dmdsecs) == 1
        assert f1.dmdsecs[0].subsection == 'dmdSec'
        assert f1.dmdsecs[0].contents.mdtype == 'DC'

        f1.add_premis_object('<premis>object</premis>')

        assert f1.amdsecs
        assert f1.amdsecs[0].subsections
        assert f1.amdsecs[0].subsections[0].subsection == 'techMD'
        assert f1.amdsecs[0].subsections[0].contents.mdtype == 'PREMIS:OBJECT'

        f1.add_premis_event('<premis>event</premis>')
        assert f1.amdsecs[0].subsections[1].subsection == 'digiprovMD'
        assert f1.amdsecs[0].subsections[1].contents.mdtype == 'PREMIS:EVENT'

        f1.add_premis_agent('<premis>agent</premis>')
        assert f1.amdsecs[0].subsections[2].subsection == 'digiprovMD'
        assert f1.amdsecs[0].subsections[2].contents.mdtype == 'PREMIS:AGENT'

        f1.add_premis_rights('<premis>rights</premis>')
        assert f1.amdsecs[0].subsections[3].subsection == 'rightsMD'
        assert f1.amdsecs[0].subsections[3].contents.mdtype == 'PREMIS:RIGHTS'

        assert len(f1.amdsecs[0].subsections) == 4
