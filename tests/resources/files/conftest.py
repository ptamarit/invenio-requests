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
def files_resource_data():
    """Example data for sending to the REST API."""
    """Input data for the Request Events Resource (REST body)."""
    return {
        "payload": {
            "content": "This is a comment.",
            "format": RequestEventFormat.HTML.value,
        }
    }
    # return {
    #     "title": "Example Request",
    #     "receiver": {"user": str(user.id)},
    # }
