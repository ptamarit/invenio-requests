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

import pytest
from flask_webpackext.manifest import (
    JinjaManifest,
    JinjaManifestEntry,
    JinjaManifestLoader,
)
from invenio_app.factory import create_ui

# from invenio_search import current_search
from invenio_requests.customizations import (
    RequestType,
)
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


# @pytest.fixture()
# def example_request(identity_simple, request_record_input_data, user1, user2):
#     """Example request."""
#     requests_service = current_requests.requests_service
#     item = requests_service.create(
#         identity_simple,
#         request_record_input_data,
#         RequestType,
#         receiver=user2.user,
#         creator=user1.user,
#     )
#     return item._request


# @pytest.fixture()
# def index_templates(running_app):
#     """Ensure the index templates are in place."""
#     list(current_search.put_templates(ignore=[400]))
