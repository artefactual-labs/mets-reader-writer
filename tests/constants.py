# -*- coding: utf-8 -*-
import uuid
import metsrw.plugins.premisrw as premisrw


EX_AGT_1_IDENTIFIER_TYPE = 'preservation system'
EX_AGT_1_IDENTIFIER_VALUE = 'Archivematica-1.6.1'
EX_AGT_1_NAME = 'Archivematica'
EX_AGT_1_TYPE = 'software'
EX_AGT_1 = (
    'agent',
    premisrw.PREMIS_META,
    (
        'agent_identifier',
        ('agent_identifier_type', EX_AGT_1_IDENTIFIER_TYPE),
        ('agent_identifier_value', EX_AGT_1_IDENTIFIER_VALUE)
    ),
    ('agent_name', EX_AGT_1_NAME),
    ('agent_type', EX_AGT_1_TYPE)
)

EX_AGT_2_IDENTIFIER_TYPE = 'repository code'
EX_AGT_2_IDENTIFIER_VALUE = 'username'
EX_AGT_2_NAME = 'username'
EX_AGT_2_TYPE = 'organization'
EX_AGT_2 = (
    'agent',
    premisrw.PREMIS_META,
    (
        'agent_identifier',
        ('agent_identifier_type', EX_AGT_2_IDENTIFIER_TYPE),
        ('agent_identifier_value', EX_AGT_2_IDENTIFIER_VALUE)
    ),
    ('agent_name', EX_AGT_2_NAME),
    ('agent_type', EX_AGT_2_TYPE)
)

EX_COMPR_EVT_AGENTS = (
    (
        'linking_agent_identifier',
        ('linking_agent_identifier_type', EX_AGT_1_IDENTIFIER_TYPE),
        ('linking_agent_identifier_value', EX_AGT_1_IDENTIFIER_VALUE),
    ),
    (
        'linking_agent_identifier',
        ('linking_agent_identifier_type', EX_AGT_2_IDENTIFIER_TYPE),
        ('linking_agent_identifier_value', EX_AGT_2_IDENTIFIER_VALUE),
    ),
)

EX_COMPR_EVT_IDENTIFIER_VALUE = str(uuid.uuid4())
EX_COMPR_EVT_TYPE = 'compression'
EX_COMPR_EVT_DATE_TIME = '2017-08-15T00:30:55'
EX_COMPR_EVT_DETAIL = (
    'program=7z; '
    'version=p7zip Version 9.20 '
    '(locale=en_US.UTF-8,Utf16=on,HugeFiles=on,2 CPUs); '
    'algorithm=bzip2')
EX_COMPR_EVT_OUTCOME_DETAIL_NOTE = (
    'Standard Output="..."; Standard Error=""')

EX_COMPR_EVT = (
    'event',
    premisrw.PREMIS_META,
    (
        'event_identifier',
        ('event_identifier_type', 'UUID'),
        ('event_identifier_value', EX_COMPR_EVT_IDENTIFIER_VALUE)
    ),
    ('event_type', EX_COMPR_EVT_TYPE),
    ('event_date_time', EX_COMPR_EVT_DATE_TIME),
    ('event_detail', EX_COMPR_EVT_DETAIL),
    (
        'event_outcome_information',
        (
            'event_outcome_detail',
            ('event_outcome_detail_note', EX_COMPR_EVT_OUTCOME_DETAIL_NOTE)
        )
    ),
    (
        'linking_agent_identifier',
        ('linking_agent_identifier_type', EX_AGT_1_IDENTIFIER_TYPE),
        ('linking_agent_identifier_value', EX_AGT_1_IDENTIFIER_VALUE)
    ),
    (
        'linking_agent_identifier',
        ('linking_agent_identifier_type', EX_AGT_2_IDENTIFIER_TYPE),
        ('linking_agent_identifier_value', EX_AGT_2_IDENTIFIER_VALUE)
    )
)

EX_ENCR_EVT_IDENTIFIER_VALUE = str(uuid.uuid4())
EX_ENCR_EVT_TYPE = 'encryption'
EX_ENCR_EVT_DATE_TIME = EX_COMPR_EVT_DATE_TIME
EX_ENCR_EVT_DETAIL = (
    'program=GPG; version=1.4.16; key=ae54fb9384asadflkj2lkjddsf')
EX_ENCR_EVT_OUTCOME = 'success'
EX_ENCR_EVT_OUTCOME_DETAIL_NOTE = EX_COMPR_EVT_OUTCOME_DETAIL_NOTE

EX_ENCR_EVT = (
    'event',
    premisrw.PREMIS_META,
    (
        'event_identifier',
        ('event_identifier_type', 'UUID'),
        ('event_identifier_value', EX_ENCR_EVT_IDENTIFIER_VALUE)
    ),
    ('event_type', EX_ENCR_EVT_TYPE),
    ('event_date_time', EX_ENCR_EVT_DATE_TIME),
    ('event_detail', EX_ENCR_EVT_DETAIL),
    (
        'event_outcome_information',
        ('event_outcome', EX_ENCR_EVT_OUTCOME),
        (
            'event_outcome_detail',
            ('event_outcome_detail_note', EX_ENCR_EVT_OUTCOME_DETAIL_NOTE)
        )
    ),
    (
        'linking_agent_identifier',
        ('linking_agent_identifier_type', EX_AGT_1_IDENTIFIER_TYPE),
        ('linking_agent_identifier_value', EX_AGT_1_IDENTIFIER_VALUE)
    ),
    (
        'linking_agent_identifier',
        ('linking_agent_identifier_type', EX_AGT_2_IDENTIFIER_TYPE),
        ('linking_agent_identifier_value', EX_AGT_2_IDENTIFIER_VALUE)
    )
)


EX_PTR_PACKAGE_TYPE = 'Archival Information Package'
EX_PTR_PATH = ('/var/archivematica/sharedDirectory/www/AIPsStore/bad2/74f3/'
               'edab/43fc/ab20/30a7/d580/ecc2/'
               't15-bad274f3-edab-43fc-ab20-30a7d580ecc2.7z')
EX_PTR_XSI_TYPE = 'premis:file'
EX_PTR_IDENTIFIER_VALUE = str(uuid.uuid4())
EX_PTR_MESSAGE_DIGEST_ALGORITHM = 'sha256'
EX_PTR_MESSAGE_DIGEST = (
    '78e4509313928d2964fe877a6a82f1ba728c171eedf696e3f5b0aed61ec547f6')
EX_PTR_SIZE = '11854'
EX_PTR_FORMAT_NAME = '7Zip format'
EX_PTR_FORMAT_REGISTRY_KEY = 'fmt/484'
EX_PTR_DATE_CREATED_BY_APPLICATION = '2017-08-15T00:30:55'
EX_PTR_AIP_SUBTYPE = 'Some strange subtype'


EX_RELATIONSHIP_1 = (
    'relationship',
    ('relationship_type', 'derivation'),
    ('relationship_sub_type', ''),
    (
        'related_object_identifier',
        ('related_object_identifier_type', 'UUID'),
        ('related_object_identifier_value', str(uuid.uuid4())),
    ),
    (
        'related_event_identifier',
        ('related_event_identifier_type', 'UUID'),
        ('related_event_identifier_value', str(uuid.uuid4())),
    ),
)

EX_RELATIONSHIP_2 = (
    'relationship',
    ('relationship_type', 'derivation'),
    ('relationship_sub_type', ''),
    (
        'related_object_identifier',
        ('related_object_identifier_type', 'UUID'),
        ('related_object_identifier_value', str(uuid.uuid4())),
    ),
    (
        'related_event_identifier',
        ('related_event_identifier_type', 'UUID'),
        ('related_event_identifier_value', str(uuid.uuid4())),
    ),
)
