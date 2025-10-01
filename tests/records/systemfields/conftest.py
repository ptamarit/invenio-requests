# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Common fixtures for systemfields tests."""

import pytest

from invenio_requests.proxies import current_requests_service as requests_service
from invenio_requests.records.api import Request


@pytest.fixture()
def example_request(database, example_request, search_clear):
    """Example request in submitted state, which allows for comments and other events."""
    example_request.status = "submitted"
    example_request.commit()
    database.session.commit()
    requests_service.indexer.index_by_id(example_request.id)
    Request.index.refresh()
    return example_request
