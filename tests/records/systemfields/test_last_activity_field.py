# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test the last activity tracking system field."""

from datetime import datetime, timedelta, timezone

import time_machine
from helpers import add_comment, create_request
from invenio_access.permissions import system_identity

from invenio_requests.proxies import current_requests_service as requests_service
from invenio_requests.records.api import Request


def test_last_activity_basic(database, example_request, user1):
    """Test basic last activity tracking functionality."""
    # Refetch to ensure we have the correct cached value
    example_request = Request.get_record(example_request.id)
    initial_updated = example_request.model.updated
    assert example_request.last_activity_at == initial_updated

    # Add a comment from user1 at a different time
    with time_machine.travel(initial_updated + timedelta(seconds=30)):
        comment1 = add_comment(example_request, user1.identity, "First comment")
    example_request = Request.get_record(example_request.id)

    # last_activity_at should now be the comment's created timestamp
    assert example_request.last_activity_at == comment1.model.created
    assert example_request.last_activity_at > initial_updated

    # Update the request (e.g., change status) at a later time
    with time_machine.travel(comment1.model.created + timedelta(seconds=30)):
        example_request.status = "accepted"
        example_request.commit()
        database.session.commit()
    example_request = Request.get_record(example_request.id)

    # last_activity_at should reflect max(model.updated, last_comment.model.created)
    assert example_request.last_activity_at == max(
        example_request.model.updated, comment1.model.created
    )


def test_last_activity_search(search, database, example_request, user1):
    """Test that search calls properly handle last_activity_at."""
    results = requests_service.search(user1.identity, expand=True).to_dict()
    assert results["hits"]["total"] == 1
    hit = results["hits"]["hits"][0]
    assert hit["last_activity_at"] is not None
    # Should equal the request's model.updated timestamp initially
    assert (
        hit["last_activity_at"]
        == example_request.model.updated.replace(tzinfo=timezone.utc).isoformat()
    )

    # Add a comment from user1 at a later time
    initial_updated = example_request.model.updated
    with time_machine.travel(initial_updated + timedelta(seconds=30)):
        comment1 = add_comment(example_request, user1.identity, "First comment")
    example_request = Request.get_record(example_request.id)

    # Should reflect the new last activity
    results = requests_service.search(user1.identity, expand=True).to_dict()
    assert results["hits"]["total"] == 1
    hit = results["hits"]["hits"][0]
    assert hit["last_activity_at"] is not None
    assert (
        hit["last_activity_at"]
        == comment1.model.created.replace(tzinfo=timezone.utc).isoformat()
    )

    # Remove the `last_activity_at` field from the index
    search.update_by_query(
        index=Request.index._name,
        body={
            "query": {
                "term": {"uuid": str(example_request.id)},
            },
            "script": "ctx._source.remove('last_activity_at')",
        },
        refresh=True,
    )

    # After removing from index, search results should show None
    # (it doesn't recalculate, just uses what's in the index)
    results = requests_service.search(user1.identity, expand=True).to_dict()
    assert results["hits"]["total"] == 1
    hit = results["hits"]["hits"][0]
    assert hit["last_activity_at"] is None


def test_last_activity_sorting(database, search_clear, user1, user2):
    """Test sorting by last activity."""
    with time_machine.travel(
        datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    ) as traveller:
        # Create first request with a comment
        request_1 = create_request(database, user1, user2, title="Request 1")
        traveller.shift(timedelta(seconds=30))
        add_comment(request_1, user1.identity, "Comment on request 1")

        # Create second request with no comments
        traveller.shift(timedelta(seconds=30))
        request_2 = create_request(database, user1, user2, title="Request 2")

        # Create third request with a new comment
        traveller.shift(timedelta(seconds=30))
        request_3 = create_request(database, user1, user2, title="Request 3")
        traveller.shift(timedelta(seconds=30))
        add_comment(request_3, user1.identity, "Comment on request 3")

        # Test newest activity sort (should be 3, 2, 1)
        results = requests_service.search(
            system_identity, params={"sort": "newestactivity"}, expand=True
        ).to_dict()
        assert results["hits"]["total"] == 3
        hits = results["hits"]["hits"]
        assert hits[0]["id"] == str(request_3.id)
        assert hits[1]["id"] == str(request_2.id)
        assert hits[2]["id"] == str(request_1.id)

        # Test oldest activity sort (should be 1, 2, 3)
        results = requests_service.search(
            system_identity, params={"sort": "oldestactivity"}, expand=True
        ).to_dict()
        assert results["hits"]["total"] == 3
        hits = results["hits"]["hits"]
        assert hits[0]["id"] == str(request_1.id)
        assert hits[1]["id"] == str(request_2.id)
        assert hits[2]["id"] == str(request_3.id)

        # Add a comment to request 2 (making it the most recent activity)
        traveller.shift(timedelta(seconds=30))
        add_comment(request_2, user1.identity, "New comment on request 2")

        # Test newest activity sort again (should now be 2, 3, 1)
        results = requests_service.search(
            system_identity, params={"sort": "newestactivity"}, expand=True
        ).to_dict()
        assert results["hits"]["total"] == 3
        hits = results["hits"]["hits"]
        assert hits[0]["id"] == str(request_2.id)
        assert hits[1]["id"] == str(request_3.id)
        assert hits[2]["id"] == str(request_1.id)

        # Test oldest activity sort again (should now be 1, 3, 2)
        results = requests_service.search(
            system_identity, params={"sort": "oldestactivity"}, expand=True
        ).to_dict()
        assert results["hits"]["total"] == 3
        hits = results["hits"]["hits"]
        assert hits[0]["id"] == str(request_1.id)
        assert hits[1]["id"] == str(request_3.id)
        assert hits[2]["id"] == str(request_2.id)
