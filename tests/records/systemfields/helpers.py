# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Helper functions for systemfields tests."""

from invenio_access.permissions import system_identity

from invenio_requests.customizations import RequestType
from invenio_requests.customizations.event_types import CommentEventType, LogEventType
from invenio_requests.proxies import current_events_service as events_service
from invenio_requests.proxies import current_requests_service as requests_service
from invenio_requests.records.api import Request, RequestEventFormat


def create_request(
    database, creator, receiver, title="Test Request", status="submitted"
):
    """Helper to create and index a request."""
    request = requests_service.create(
        creator.identity,
        {"type": "base-request", "title": title},
        RequestType,
        receiver=receiver.user,
        creator=creator.user,
    )._request
    request.status = status
    request.commit()
    database.session.commit()
    requests_service.indexer.index_by_id(request.id)
    return request


# TODO: This helper is only used in tests.
def add_comment(request, identity, content):
    """Helper to add a comment to a request."""
    event = events_service.create(
        identity,
        request.id,
        {
            "type": CommentEventType.type_id,
            "payload": {"content": content, "format": "html"},
        },
        CommentEventType,
    )

    # Force index refresh
    Request.index.refresh()

    return event._record


def add_log_event(request, identity, content):
    """Helper to add a system event to a request."""
    event = events_service.create(
        system_identity,
        request.id,
        {
            "type": LogEventType.type_id,
            "created_by": system_identity,
            "payload": {
                "content": content,
                "format": RequestEventFormat.HTML.value,
                "event": "LOG_EVENT",
            },
        },
        LogEventType,
    )

    # Force index refresh
    Request.index.refresh()

    return event._record
