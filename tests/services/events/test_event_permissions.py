# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Permission tests."""

import pytest
from invenio_records_resources.services.errors import PermissionDeniedError

from invenio_requests.customizations.event_types import CommentEventType, LogEventType
from invenio_requests.errors import RequestLockedError
from invenio_requests.records.api import RequestEvent


def test_creator_and_receiver_can_comment(
    app,
    identity_simple,
    identity_simple_2,
    identity_stranger,
    request_events_service,
    events_service_data,
    submit_request,
):
    request = submit_request(identity_simple)
    request_id = request.id
    comment = events_service_data["comment"]

    # Creator
    assert request_events_service.create(
        identity_simple, request_id, comment, CommentEventType
    )
    # Receiver
    assert request_events_service.create(
        identity_simple_2, request_id, comment, CommentEventType
    )
    # Stranger
    with pytest.raises(PermissionDeniedError):
        request_events_service.create(
            identity_stranger, request_id, comment, CommentEventType
        )


def test_only_commenter_can_update_comment(
    app,
    identity_simple,
    identity_simple_2,
    identity_stranger,
    request_events_service,
    events_service_data,
    example_request,
):
    request_id = example_request.id
    comment = events_service_data["comment"]

    item = request_events_service.create(
        identity_simple, request_id, comment, CommentEventType
    )
    comment_id = item.id

    # Stranger
    with pytest.raises(PermissionDeniedError):
        request_events_service.update(identity_stranger, comment_id, comment)
    # Receiver
    with pytest.raises(PermissionDeniedError):
        request_events_service.update(identity_simple_2, comment_id, comment)
    # Commenter
    assert request_events_service.update(identity_simple, comment_id, comment)


def test_only_commenter_can_delete_comment(
    app,
    identity_simple,
    identity_simple_2,
    identity_stranger,
    request_events_service,
    events_service_data,
    example_request,
):
    request_id = example_request.id
    comment = events_service_data["comment"]

    item_1 = request_events_service.create(
        identity_simple, request_id, comment, CommentEventType
    )
    comment_id_1 = item_1.id
    item_2 = request_events_service.create(
        identity_simple, request_id, comment, CommentEventType
    )
    comment_id_2 = item_2.id

    # Stranger
    with pytest.raises(PermissionDeniedError):
        request_events_service.delete(identity_stranger, comment_id_1)
    # Receiver
    with pytest.raises(PermissionDeniedError):
        request_events_service.delete(identity_simple_2, comment_id_1)
    # Commenter
    assert request_events_service.delete(identity_simple, comment_id_2)


def test_creator_can_see_timeline(
    app,
    identity_simple,
    identity_simple_2,
    identity_stranger,
    request_events_service,
    events_service_data,
    example_request,
):
    request_id = example_request.id
    comment = events_service_data["comment"]

    request_events_service.create(
        identity_simple, request_id, comment, CommentEventType
    )
    RequestEvent.index.refresh()

    # Stranger
    with pytest.raises(PermissionDeniedError):
        request_events_service.search(identity_stranger, request_id)
    # Receiver
    with pytest.raises(PermissionDeniedError):
        request_events_service.search(identity_simple_2, request_id)
    # Creator
    assert list(request_events_service.search(identity_simple, request_id))


def test_receiver_can_see_timeline_of_open_request(
    app,
    identity_simple,
    identity_simple_2,
    identity_stranger,
    request_events_service,
    events_service_data,
    submit_request,
):
    request = submit_request(identity_simple)
    request_id = request.id
    comment = events_service_data["comment"]

    request_events_service.create(
        identity_simple, request_id, comment, CommentEventType
    )
    RequestEvent.index.refresh()

    # Stranger
    with pytest.raises(PermissionDeniedError):
        request_events_service.search(identity_stranger, request_id)
    # Receiver
    assert list(request_events_service.search(identity_simple_2, request_id))


def test_commenting_on_locked_request(
    app,
    identity_simple,
    identity_simple_2,
    identity_stranger,
    request_events_service,
    requests_service,
    events_service_data,
    request_with_locking_enabled,
    monkeypatch,
):
    monkeypatch.setitem(app.config, "REQUESTS_LOCKING_ENABLED", True)
    request = request_with_locking_enabled
    comment = events_service_data["comment"]

    # Creator can submit comment
    item = request_events_service.create(
        identity_simple, request.id, comment, CommentEventType
    )
    comment_id = item.id

    requests_service.lock_request(identity_simple_2, request.id)

    # Refresh index
    RequestEvent.index.refresh()

    # Receiver cannot submit comment
    with pytest.raises(RequestLockedError):
        request_events_service.create(
            identity_simple_2, request.id, comment, CommentEventType
        )
    # Creator cannot edit comment
    with pytest.raises(RequestLockedError):
        request_events_service.update(identity_simple, comment_id, comment)
    # Stranger cannot submit comment
    with pytest.raises(PermissionDeniedError):
        request_events_service.create(
            identity_stranger, request.id, comment, CommentEventType
        )
    # Stranger cannot submit log event manually
    with pytest.raises(PermissionDeniedError):
        request_events_service.create(
            identity_stranger, request.id, {"payload": {"event": "test"}}, LogEventType
        )

    # Log events are not blocked by locked request
    # For eg. decline action can be executed on locked request
    requests_service.execute_action(identity_simple_2, request.id, "decline")
    RequestEvent.index.refresh()

    results = request_events_service.search(identity_simple_2, request.id)
    assert 3 == results.total  # comment + locked + declined
    # Creation and submission events are not logged because they have log_event=False
