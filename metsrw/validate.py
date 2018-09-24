# -*- coding: utf-8 -*-
import os

from lxml import etree, isoschematron
import six

from .utils import NAMESPACES

METS_XSD_PATH = 'resources/mets.xsd'

# Right now there are two different schematron files for validating
# Archivematica-generated METS files vs Archivematica-generated METS pointer
# files. These could be consolidated to one.
AM_SCT_PATH = 'resources/archivematica_mets_schematron.xml'
AM_PNTR_SCT_PATH = 'resources/archivematica_mets_pointer_file_schematron.xml'


def _get_file_path(path):
    if not os.path.isfile(path):
        path_2 = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            path)
        if not os.path.isfile(path_2):
            raise ValueError(
                'There is no (schema) file at either {} or {}'.format(
                    path, path_2))
        return path_2
    return path


def get_schematron(sct_path):
    """Return an lxml ``isoschematron.Schematron()`` instance using the
    schematron file at ``sct_path``.
    """
    sct_path = _get_file_path(sct_path)
    parser = etree.XMLParser(remove_blank_text=True)
    sct_doc = etree.parse(sct_path, parser=parser)
    return isoschematron.Schematron(sct_doc, store_report=True)


def validate(mets_doc, xmlschema=METS_XSD_PATH, schematron=AM_SCT_PATH):
    """Validate a METS file using both an XMLSchema (.xsd) schema and a
    schematron schema, the latter of which typically places additional
    constraints on what a METS file can look like.
    """
    is_xsd_valid, xsd_error_log = xsd_validate(mets_doc, xmlschema=xmlschema)
    is_sct_valid, sct_report = schematron_validate(
        mets_doc, schematron=schematron)
    valid = is_xsd_valid and is_sct_valid
    report = {
        'is_xsd_valid': is_xsd_valid,
        'is_sct_valid': is_sct_valid,
        'xsd_error_log': xsd_error_log,
        'sct_report': sct_report
    }
    report['report'] = report_string(report)
    return valid, report


def get_xmlschema(xmlschema, mets_doc):
    """Return a ``class::lxml.etree.XMLSchema`` instance given the path to the
    XMLSchema (.xsd) file in ``xmlschema`` and the
    ``class::lxml.etree._ElementTree`` instance ``mets_doc`` representing the
    METS file being parsed. The complication here is that the METS file to be
    validated via the .xsd file may reference additional schemata via
    ``xsi:schemaLocation`` attributes. We have to find all of these and import
    them from within the returned XMLSchema.

    For the solution that this is based on, see:
    http://code.activestate.com/recipes/578503-validate-xml-with-schemalocation/

    For other descriptions of the problem, see:
    - https://groups.google.com/forum/#!topic/archivematica/UBS1ay-g_tE
    - https://stackoverflow.com/questions/26712645/xml-type-definition-is-absent
    - https://stackoverflow.com/questions/2979824/in-document-schema-declarations-and-lxml
    """
    xsd_path = _get_file_path(xmlschema)
    xmlschema = etree.parse(xsd_path)
    schema_locations = set(
        mets_doc.xpath('//*/@xsi:schemaLocation', namespaces=NAMESPACES))
    for schema_location in schema_locations:
        namespaces_locations = schema_location.strip().split()
        for namespace, location in zip(*[iter(namespaces_locations)] * 2):
            if namespace == NAMESPACES['mets']:
                continue
            xs_import = etree.Element(
                '{http://www.w3.org/2001/XMLSchema}import')
            xs_import.attrib['namespace'] = namespace
            xs_import.attrib['schemaLocation'] = location
            xmlschema.getroot().insert(0, xs_import)
    return etree.XMLSchema(xmlschema)


def xsd_validate(mets_doc, xmlschema=METS_XSD_PATH):
    xmlschema = get_xmlschema(xmlschema, mets_doc)
    is_valid = xmlschema.validate(mets_doc)
    error_log = xmlschema.error_log
    return is_valid, error_log


def schematron_validate(mets_doc, schematron=AM_SCT_PATH):
    """Validate a METS file using a schematron schema. Return a boolean
    indicating validity and a report as an ``lxml.ElementTree`` instance.
    """
    if isinstance(schematron, six.string_types):
        schematron = get_schematron(schematron)
    is_valid = schematron.validate(mets_doc)
    report = schematron.validation_report
    return is_valid, report


def sct_report_string(report):
    """Return a human-readable string representation of the error report
    returned by lxml's schematron validator.
    """
    ret = []
    namespaces = {'svrl': 'http://purl.oclc.org/dsdl/svrl'}
    for index, failed_assert_el in enumerate(report.findall(
            'svrl:failed-assert', namespaces=namespaces)):
        ret.append('{}. {}'.format(
            index + 1,
            failed_assert_el.find('svrl:text', namespaces=namespaces).text))
        ret.append('   test: {}'.format(failed_assert_el.attrib['test']))
        ret.append('   location: {}'.format(failed_assert_el.attrib['location']))
        ret.append('\n')
    return '\n'.join(ret)


def xsd_error_log_string(xsd_error_log):
    """Return a human-readable string representation of the error log
    returned by lxml's XMLSchema validator.
    """
    ret = []
    for error in xsd_error_log:
        ret.append('ERROR ON LINE {}: {}'.format(
            error.line, error.message.encode('utf-8')))
    return '\n'.join(ret)


def report_string(report):
    """Return a human-readable string representation of all of the validation
    errors.
    """
    return (
        'Schematron Error(s):\n' +
        sct_report_string(report['sct_report']) +
        '\n\nXMLSchema (xsd) Error(s):\n' +
        xsd_error_log_string(report['xsd_error_log']))
