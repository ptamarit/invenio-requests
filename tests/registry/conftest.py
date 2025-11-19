# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CESNET i.a.l.e.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""App fixture with test entrypoints."""

import pytest
from invenio_app.factory import create_api


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return create_api


@pytest.fixture(scope="module")
def extra_entry_points():
    """Extra entry points to load the mock_module features."""
    return {
        "invenio_requests.types": [
            "mock_module = tests.mock_module:MockRequestType",
        ],
        "invenio_requests.event_types": [
            "mock_module = tests.mock_module:MockEventType",
        ],
        "invenio_requests.entity_resolvers": [
            "mock_module = tests.mock_module:MockResolver",
        ],
    }
