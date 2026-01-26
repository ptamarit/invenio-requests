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
from flask_webpackext.manifest import (
    JinjaManifest,
    JinjaManifestEntry,
    JinjaManifestLoader,
)
from invenio_app.factory import create_ui

from invenio_requests.proxies import current_requests


#
# Mock the webpack manifest to avoid having to compile the full assets.
#
class MockJinjaManifest(JinjaManifest):
    """Mock manifest."""

    def __getitem__(self, key):
        """Get a manifest entry."""
        return JinjaManifestEntry(key, [key])

    def __getattr__(self, name):
        """Get a manifest entry."""
        return JinjaManifestEntry(name, [name])


class MockManifestLoader(JinjaManifestLoader):
    """Manifest loader creating a mocked manifest."""

    def load(self, filepath):
        """Load the manifest."""
        return MockJinjaManifest()


@pytest.fixture(scope="module")
def app_config(app_config):
    """Create test app."""
    app_config["WEBPACKEXT_MANIFEST_LOADER"] = MockManifestLoader
    return app_config


@pytest.fixture(scope="module")
def create_app():
    """Create test app."""
    return create_ui


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
