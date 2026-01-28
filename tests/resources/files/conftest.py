# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Request Files Resource conftest."""

import pytest

from invenio_requests.records.api import RequestEventFormat


@pytest.fixture()
def headers_upload():
    """Default headers for uploads."""
    return {
        "content-type": "application/octet-stream",
        "accept": "application/json",
    }


@pytest.fixture()
def events_resource_data():
    """Input data for the Request Events Resource (REST body)."""
    return {
        "payload": {
            "content": "This is a comment.",
            "format": RequestEventFormat.HTML.value,
        }
    }
