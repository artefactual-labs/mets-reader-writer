# -*- coding: utf8 -*-
"""Tests for the metsrw.validate module."""

from __future__ import print_function

import os

import pytest

import metsrw


def test_get_schematron(mocker):
    bad_path = 'some/nonexistent/path/'
    with mocker.patch('metsrw.get_file_path') as get_file_path:
        with pytest.raises(ValueError):
            metsrw.get_schematron(bad_path)
            get_file_path.assert_called_once_with(bad_path)

    with mocker.patch('metsrw.get_file_path') as get_file_path:
        mocker.patch.object(os.path, 'isfile', return_value=True)
        with pytest.raises(IOError):
            metsrw.get_schematron(bad_path)
            get_file_path.assert_called_once_with(bad_path)

    def mockisfile(path):
        return not (path == bad_path)

    mocker.patch.object(os.path, 'isfile', mockisfile)
    with pytest.raises(IOError):
        metsrw.get_schematron(bad_path)
        assert os.path.isfile.call_count == 2
