# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration for the UI application.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

from io import BytesIO

import pytest

from invenio_requests.proxies import current_requests


@pytest.fixture()
def example_request_file(example_request, identity_simple, location):
    """Example request file."""
    # Passing the `location` fixture to make sure that a default bucket location is defined.
    assert location.default == True

    key = "filename.ext"
    data = b"test"
    length = 4

    request_files_service = current_requests.request_files_service
    file_details = request_files_service.create_file(
        identity=identity_simple,
        id_=example_request.id,
        key=key,
        stream=BytesIO(data),
        content_length=length,
    )

    return {
        "key": file_details["key"],
        "data": data,
    }
