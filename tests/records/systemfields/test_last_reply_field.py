# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test the last reply tracking system field."""

from datetime import timezone

import pytest
from invenio_access.permissions import system_identity

from invenio_requests.customizations.event_types import CommentEventType, LogEventType
from invenio_requests.proxies import current_events_service as events_service
from invenio_requests.proxies import current_requests_service as requests_service
from invenio_requests.records.api import Request, RequestEventFormat


@pytest.fixture()
def example_request(database, example_request, search_clear):
    """Example request in submitted state, which allows for comments and other events."""
    example_request.status = "submitted"
    example_request.commit()
    database.session.commit()
    requests_service.indexer.index_by_id(example_request.id)
    Request.index.refresh()
    return example_request


def _add_comment(request, identity, content):
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


def _add_log_event(request, identity, content):
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


def test_last_reply_tracking_basic(example_request, user1, user2):
    """Test basic last reply tracking functionality."""
    # Initially no replies
    assert example_request.last_reply is None

    # Add a comment from user1 (the creator)
    comment1 = _add_comment(example_request, user1.identity, "First comment")
    example_request = Request.get_record(example_request.id)

    assert example_request.last_reply is not None
    assert example_request.last_reply.created_by.resolve() == user1.user
    assert example_request.last_reply.created == comment1.created
    assert example_request.last_reply.id == comment1.id

    # Add another comment from user2 (the receiver)
    comment2 = _add_comment(example_request, user2.identity, "Second comment")
    example_request = Request.get_record(example_request.id)

    assert example_request.last_reply.created_by.resolve() == user2.user
    assert example_request.last_reply.created == comment2.created
    assert example_request.last_reply.id == comment2.id


def test_last_reply_search(search, example_request, user1):
    """Test that search calls use the pre-dumped last reply."""
    results = requests_service.search(user1.identity, expand=True).to_dict()
    assert results["hits"]["total"] == 1
    hit = results["hits"]["hits"][0]
    assert hit["last_reply"] is None

    # Add a comment from user1 (the creator)
    comment1 = _add_comment(example_request, user1.identity, "First comment")
    example_request = Request.get_record(example_request.id)

    # Should reflect the last reply
    results = requests_service.search(user1.identity, expand=True).to_dict()
    assert results["hits"]["total"] == 1
    hit = results["hits"]["hits"][0]
    assert hit["last_reply"] is not None
    assert hit["last_reply"]["id"] == str(comment1.id)
    assert hit["last_reply"]["created_by"]["user"] == str(user1.user.id)
    assert (
        hit["last_reply"]["created"]
        == comment1.created.replace(tzinfo=timezone.utc).isoformat()
    )

    # On purpose remove the `last_reply` field to check that we don't recalculate and
    # fetch from the DB.
    search.update_by_query(
        index=Request.index._name,
        body={
            "query": {
                "term": {"uuid": str(example_request.id)},
            },
            "script": "ctx._source.remove('last_reply')",
        },
        refresh=True,
    )

    # Since the index doesn't have the `last_reply` field it should return `None` and
    # not recompute it from the DB.
    results = requests_service.search(user1.identity, expand=True).to_dict()
    assert results["hits"]["total"] == 1
    hit = results["hits"]["hits"][0]
    assert hit["last_reply"] is None


def test_system_comments_excluded(example_request, user1):
    """Test that system-generated comments are excluded from last reply."""
    # Add user comment
    _add_comment(example_request, user1.identity, "User comment")
    example_request = Request.get_record(example_request.id)

    assert example_request.last_reply.created_by.resolve() == user1.user
    original_reply = example_request.last_reply

    # Add system event (e.g., log event)
    _add_log_event(example_request, system_identity, "Auto-accepted")
    example_request = Request.get_record(example_request.id)

    # Last reply should still be the user comment
    assert example_request.last_reply.created_by.resolve() == user1.user
    assert example_request.last_reply.id == original_reply.id


def test_search_index_last_reply(example_request, user2, search_clear):
    """Test that last reply object is properly indexed."""
    # Add comment
    comment_event = _add_comment(example_request, user2.identity, "Reply")

    def _assert_hit_eq(hit):
        assert hit["id"] == str(example_request.id)
        assert hit["last_reply"] is not None
        assert hit["last_reply"]["created_by"]["user"] == str(user2.user.id)
        assert (
            hit["last_reply"]["created"]
            == comment_event.created.replace(tzinfo=timezone.utc).isoformat()
        )
        assert hit["last_reply"]["id"] == str(comment_event.id)
        expanded = hit["expanded"]["last_reply"]
        assert expanded is not None
        assert expanded["created_by"]["id"] == str(user2.user.id)
        assert {"profile", "email", "username"} <= expanded["created_by"].keys()

    # Search by all requests first to check indexing
    results = requests_service.search(system_identity, expand=True).to_dict()

    assert results["hits"]["total"] == 1
    _assert_hit_eq(results["hits"]["hits"][0])

    # Search by last reply creator
    results = requests_service.search(
        system_identity,
        params={"q": f"last_reply.created_by.user:{user2.user.id}"},
        expand=True,
    ).to_dict()

    assert results["hits"]["total"] == 1
    _assert_hit_eq(results["hits"]["hits"][0])
