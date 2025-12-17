# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Resource tests."""

import copy

from invenio_requests.customizations.event_types import CommentEventType, LogEventType
from invenio_requests.records.api import RequestEvent


def assert_api_response_json(expected_json, received_json):
    """Assert the REST API response's json."""
    # We don't compare dynamic times at this point
    received_json.pop("created")
    received_json.pop("updated")
    assert expected_json == received_json


def assert_api_response(response, code, json):
    """Assert the REST API response."""
    assert code == response.status_code
    assert_api_response_json(json, response.json)


def test_simple_comment_flow(
    app, client_logged_as, headers, events_resource_data, example_request
):
    request_id = example_request.id

    # User 2 cannot comment yet (the record's still a draft)
    client = client_logged_as("user2@example.org")
    response = client.post(
        f"/requests/{request_id}/comments", headers=headers, json=events_resource_data
    )
    assert response.status_code == 403

    # User 1 comments (the creator is allowed to comment on their draft requests)
    client = client_logged_as("user1@example.org")
    response = client.post(
        f"/requests/{request_id}/comments", headers=headers, json=events_resource_data
    )

    comment_id = response.json["id"]
    expected_json_1 = {
        **events_resource_data,
        "created_by": {"user": "1"},
        "id": comment_id,
        "links": {
            "reply": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}/reply",  # noqa
            "replies": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}/replies",  # noqa
            "self": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}",  # noqa
            "self_html": f"https://127.0.0.1:5000/requests/{request_id}#commentevent-{comment_id}",
        },
        "parent_id": None,
        "permissions": {
            "can_update_comment": True,
            "can_delete_comment": True,
            "can_reply_comment": True,
        },
        "revision_id": 1,
        "type": CommentEventType.type_id,
    }
    assert_api_response(response, 201, expected_json_1)

    # User 1 reads comment
    response = client.get(
        f"/requests/{request_id}/comments/{comment_id}",
        headers=headers,
    )
    assert_api_response(response, 200, expected_json_1)

    # User 1 submits the request
    response = client.post(f"/requests/{request_id}/actions/submit", headers=headers)
    assert response.status_code == 200

    # User 2 comments
    client = client_logged_as("user2@example.org")
    response = client.post(
        f"/requests/{request_id}/comments", headers=headers, json=events_resource_data
    )
    comment_id = response.json["id"]
    revision_id = response.json["revision_id"]

    # User 2 updates comments
    data = copy.deepcopy(events_resource_data)
    data["payload"]["content"] = "I've revised my comment."
    revision_headers = copy.deepcopy(headers)
    revision_headers["if_match"] = revision_id
    response = client.put(
        f"/requests/{request_id}/comments/{comment_id}",
        headers=revision_headers,
        json=data,
    )
    expected_json_2 = {
        **data,
        "created_by": {"user": "2"},
        "id": comment_id,
        "links": {
            "reply": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}/reply",  # noqa
            "replies": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}/replies",  # noqa
            "self": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}",  # noqa
            "self_html": f"https://127.0.0.1:5000/requests/{request_id}#commentevent-{comment_id}",
        },
        "parent_id": None,
        "permissions": {
            "can_update_comment": True,
            "can_delete_comment": True,
            "can_reply_comment": True,
        },
        "revision_id": 2,
        "type": CommentEventType.type_id,
    }
    assert_api_response(response, 200, expected_json_2)

    # User 2 deletes comments
    revision_headers["if_match"] = 2
    response = client.delete(
        f"/requests/{request_id}/comments/{comment_id}",
        headers=revision_headers,
    )
    assert 204 == response.status_code
    assert b"" == response.data

    RequestEvent.index.refresh()

    # User 2 gets the timeline (will be sorted)
    response = client.get(f"/requests/{request_id}/timeline", headers=headers)
    assert 200 == response.status_code
    assert 2 == response.json["hits"]["total"]
    # User 2 cannot update or delete the comment created by user 1
    # Timeline includes children fields
    expected_json_1_with_updated_perms = {
        **expected_json_1,
        "children": [],
        "children_count": 0,
        "permissions": {
            "can_update_comment": False,
            "can_delete_comment": False,
            "can_reply_comment": True,
        },
    }
    assert_api_response_json(
        expected_json_1_with_updated_perms, response.json["hits"]["hits"][0]
    )
    expected_json_3 = {
        "created_by": {"user": "2"},
        "revision_id": 2,
        "payload": {
            "content": "comment was deleted",
            "event": "comment_deleted",
            "format": "html",
        },
        "type": LogEventType.type_id,
    }

    res = response.json["hits"]["hits"][1]
    assert expected_json_3["payload"] == res["payload"]
    assert expected_json_3["created_by"] == res["created_by"]
    assert expected_json_3["type"] == res["type"]


def test_timeline_links(
    client_logged_as, events_resource_data, example_request, headers
):
    """Tests the links for the timeline (search) endpoint."""
    client = client_logged_as("user1@example.org")
    request_id = example_request.id
    client.post(
        f"/requests/{request_id}/comments", headers=headers, json=events_resource_data
    )

    response = client.get(f"/requests/{request_id}/timeline", headers=headers)
    search_record_links = response.json["links"]

    expected_links = {
        # NOTE: Variations are covered in records-resources
        "self": f"https://127.0.0.1:5000/api/requests/{request_id}/timeline?page=1&size=25&sort=oldest",  # noqa
    }
    assert expected_links == search_record_links


def test_empty_comment(
    app, client_logged_as, headers, events_resource_data, example_request
):
    client = client_logged_as("user1@example.org")
    request_id = example_request.id

    # Comment no payload is an error
    response = client.post(f"/requests/{request_id}/comments", headers=headers)

    expected_json = {
        "errors": [
            {"field": "payload", "messages": ["Missing data for required field."]}
        ],
        "message": "A validation error occurred.",
        "status": 400,
    }
    assert 400 == response.status_code
    assert expected_json == response.json

    # Comment {} is an error
    response = client.post(f"/requests/{request_id}/comments", headers=headers, json={})
    assert 400 == response.status_code
    assert expected_json == response.json

    # Comment empty content is an error
    data = copy.deepcopy(events_resource_data)
    data["payload"]["content"] = ""
    response = client.post(
        f"/requests/{request_id}/comments", headers=headers, json=data
    )
    assert 400 == response.status_code
    expected_json = {
        **expected_json,
        "errors": [
            {"field": "payload.content", "messages": ["Shorter than minimum length 1."]}
        ],
    }
    assert expected_json == response.json

    # Update with empty comment is an error
    # (first create one correctly)
    data["payload"]["content"] = "This is a comment."
    response = client.post(
        f"/requests/{request_id}/comments", headers=headers, json=data
    )
    comment_id = response.json["id"]
    data["payload"]["content"] = ""
    response = client.put(
        f"/requests/{request_id}/comments/{comment_id}", headers=headers, json=data
    )
    assert 400 == response.status_code
    assert expected_json == response.json


def test_locked_request_comments(
    app,
    client_logged_as,
    headers,
    events_resource_data,
    request_with_locking_enabled,
    monkeypatch,
):
    monkeypatch.setitem(app.config, "REQUESTS_LOCKING_ENABLED", True)
    client = client_logged_as("user2@example.org")
    request_id = request_with_locking_enabled.id

    # Lock request
    response = client.get(f"/requests/{request_id}/lock", headers=headers)
    assert response.status_code == 204

    # Comment on locked request is an error
    response = client.post(
        f"/requests/{request_id}/comments", headers=headers, json=events_resource_data
    )
    assert response.status_code == 403


def test_threaded_comments_with_indexing(
    app, client_logged_as, headers, events_resource_data, example_request
):
    """Test creating threaded comments (replies) and verify indexing of children."""
    client = client_logged_as("user1@example.org")
    request_id = example_request.id

    # Step 1: Create a parent comment
    parent_data = copy.deepcopy(events_resource_data)
    parent_data["payload"]["content"] = "This is the parent comment."
    response = client.post(
        f"/requests/{request_id}/comments", headers=headers, json=parent_data
    )
    assert response.status_code == 201
    parent_comment_id = response.json["id"]
    assert response.json["payload"]["content"] == "This is the parent comment."
    # Parent should have no parent_id
    assert "parent_id" not in response.json or response.json.get("parent_id") is None

    # Step 2: Create first reply (child comment) using the reply endpoint
    reply1_data = copy.deepcopy(events_resource_data)
    reply1_data["payload"]["content"] = "This is the first reply."
    response = client.post(
        f"/requests/{request_id}/comments/{parent_comment_id}/reply",
        headers=headers,
        json=reply1_data,
    )
    assert response.status_code == 201
    reply1_id = response.json["id"]
    assert response.json["payload"]["content"] == "This is the first reply."
    # Verify parent_id is set in response
    assert response.json.get("parent_id") == parent_comment_id

    # Step 3: Create second reply (child comment) using the reply endpoint
    reply2_data = copy.deepcopy(events_resource_data)
    reply2_data["payload"]["content"] = "This is the second reply."
    response = client.post(
        f"/requests/{request_id}/comments/{parent_comment_id}/reply",
        headers=headers,
        json=reply2_data,
    )
    assert response.status_code == 201
    reply2_id = response.json["id"]
    assert response.json["payload"]["content"] == "This is the second reply."
    assert response.json.get("parent_id") == parent_comment_id

    # Step 4: Refresh the search index to ensure all events are indexed
    RequestEvent.index.refresh()

    # Step 5: Retrieve timeline to verify indexing
    response = client.get(f"/requests/{request_id}/timeline", headers=headers)
    assert response.status_code == 200
    hits = response.json["hits"]["hits"]
    assert len(hits) == 1

    # Find the parent comment in the results
    parent_event = hits[0]

    # Step 6: Verify parent has children array
    assert "children" in parent_event, "Parent event missing 'children' field"

    children = parent_event["children"]
    assert len(children) == 2, f"Expected 2 children, got {len(children)}"

    # Verify child content matches what we created (ordered by most recent first)
    reply1_event = children[1]  # Older reply is second
    reply2_event = children[0]  # Most recent reply is first
    assert "This is the first reply." == reply1_event["payload"]["content"]
    assert "This is the second reply." == reply2_event["payload"]["content"]

    # Step 8: Update a child comment and verify re-indexing
    updated_reply_data = copy.deepcopy(events_resource_data)
    updated_reply_data["payload"]["content"] = "This is the updated first reply."
    response = client.put(
        f"/requests/{request_id}/comments/{reply1_id}",
        headers=headers,
        json=updated_reply_data,
    )
    assert response.status_code == 200
    assert response.json["payload"]["content"] == "This is the updated first reply."

    # Refresh index and verify parent's children reflect the update
    RequestEvent.index.refresh()
    response = client.get(f"/requests/{request_id}/timeline", headers=headers)
    assert response.status_code == 200
    hits = response.json["hits"]["hits"]

    parent_event = next((hit for hit in hits if hit["id"] == parent_comment_id), None)
    assert parent_event is not None
    assert "children" in parent_event
    children = parent_event["children"]

    # Find the updated child in children array
    updated_child = next((c for c in children if c["id"] == reply1_id), None)
    assert updated_child is not None
    assert (
        updated_child["payload"]["content"] == "This is the updated first reply."
    ), "Parent's children array not updated after child modification"


def test_delete_child_comment_preserves_parent_child(
    app, client_logged_as, headers, events_resource_data, example_request
):
    """Test deleting a child comment via REST API preserves parent-child structure."""
    client = client_logged_as("user1@example.org")
    request_id = example_request.id

    # Create parent comment
    parent_data = copy.deepcopy(events_resource_data)
    parent_data["payload"]["content"] = "Parent comment"
    response = client.post(
        f"/requests/{request_id}/comments", headers=headers, json=parent_data
    )
    assert response.status_code == 201
    parent_comment_id = response.json["id"]

    # Create two child replies using reply endpoint
    reply1_data = copy.deepcopy(events_resource_data)
    reply1_data["payload"]["content"] = "First reply"
    response = client.post(
        f"/requests/{request_id}/comments/{parent_comment_id}/reply",
        headers=headers,
        json=reply1_data,
    )
    assert response.status_code == 201
    reply1_id = response.json["id"]
    assert response.json["parent_id"] == parent_comment_id

    reply2_data = copy.deepcopy(events_resource_data)
    reply2_data["payload"]["content"] = "Second reply"
    response = client.post(
        f"/requests/{request_id}/comments/{parent_comment_id}/reply",
        headers=headers,
        json=reply2_data,
    )
    assert response.status_code == 201
    reply2_id = response.json["id"]
    assert response.json["parent_id"] == parent_comment_id

    # Refresh index
    RequestEvent.index.refresh()

    # Delete the first child comment
    response = client.delete(
        f"/requests/{request_id}/comments/{reply1_id}", headers=headers
    )
    assert response.status_code == 204

    # Refresh index
    RequestEvent.index.refresh()

    # Verify the deleted child is still a CommentEventType with deleted content
    response = client.get(
        f"/requests/{request_id}/comments/{reply1_id}", headers=headers
    )
    assert response.status_code == 200
    deleted_child = response.json
    assert deleted_child["type"] == LogEventType.type_id
    assert deleted_child["payload"]["content"] == "comment was deleted"
    # Verify parent-child relationship preserved
    assert deleted_child["parent_id"] == parent_comment_id

    # Get timeline and verify parent's children array
    response = client.get(f"/requests/{request_id}/timeline", headers=headers)
    assert response.status_code == 200
    hits = response.json["hits"]["hits"]

    parent_event = next((hit for hit in hits if hit["id"] == parent_comment_id), None)
    assert parent_event is not None
    assert "children" in parent_event

    children = parent_event["children"]
    assert len(children) == 2  # Both children still present

    # Verify both are CommentEventType (one deleted, one active)
    child_types = {child["type"] for child in children}
    assert child_types == {CommentEventType.type_id, LogEventType.type_id}

    # Verify deleted child maintains parent_id and has deleted content
    deleted_child_in_array = next((c for c in children if c["id"] == reply1_id), None)
    assert deleted_child_in_array is not None
    assert deleted_child_in_array["type"] == LogEventType.type_id
    assert deleted_child_in_array["payload"]["content"] == "comment was deleted"
    assert deleted_child_in_array["parent_id"] == parent_comment_id

    # Verify active child is unchanged
    active_child = next((c for c in children if c["id"] == reply2_id), None)
    assert active_child is not None
    assert active_child["type"] == CommentEventType.type_id
    assert active_child["payload"]["content"] == "Second reply"


def test_nested_children_not_allowed(
    app, client_logged_as, headers, events_resource_data, example_request
):
    """Test that 2-level nesting (reply to reply) is NOT allowed."""
    client = client_logged_as("user1@example.org")
    request_id = example_request.id

    # Step 1: Create parent comment
    parent_data = copy.deepcopy(events_resource_data)
    parent_data["payload"]["content"] = "This is the parent comment."
    response = client.post(
        f"/requests/{request_id}/comments", headers=headers, json=parent_data
    )
    assert response.status_code == 201
    parent_comment_id = response.json["id"]
    assert response.json["payload"]["content"] == "This is the parent comment."
    assert "parent_id" not in response.json or response.json.get("parent_id") is None

    # Step 2: Create first-level reply (child) using reply endpoint - this should succeed
    child_data = copy.deepcopy(events_resource_data)
    child_data["payload"]["content"] = "This is a reply to the parent."
    response = client.post(
        f"/requests/{request_id}/comments/{parent_comment_id}/reply",
        headers=headers,
        json=child_data,
    )
    assert response.status_code == 201
    child_comment_id = response.json["id"]
    assert response.json["payload"]["content"] == "This is a reply to the parent."
    assert response.json.get("parent_id") == parent_comment_id

    # Step 3: Attempt to create second-level reply (grandchild - reply to child)
    # This should FAIL with a 400 error
    grandchild_data = copy.deepcopy(events_resource_data)
    grandchild_data["payload"]["content"] = "This is a reply to the reply."
    response = client.post(
        f"/requests/{request_id}/comments/{child_comment_id}/reply",
        headers=headers,
        json=grandchild_data,
    )

    # Verify the request is rejected
    assert response.status_code == 400
    assert "errors" in response.json or "message" in response.json
    # The error message should indicate nested children are not allowed
    error_message = response.json.get("message", "").lower()
    assert "nested" in error_message or "not allowed" in error_message

    # Step 4: Refresh index and verify only 1-level nesting exists
    RequestEvent.index.refresh()

    # Retrieve timeline
    response = client.get(f"/requests/{request_id}/timeline", headers=headers)
    assert response.status_code == 200
    all_hits = response.json["hits"]["hits"]

    # Filter to only top-level comments (no parent_id)
    top_level_hits = [hit for hit in all_hits if not hit.get("parent_id")]
    assert len(top_level_hits) == 1, "Timeline should show only 1 top-level comment"

    # Verify parent comment structure
    parent_event = top_level_hits[0]
    assert parent_event["id"] == parent_comment_id
    assert parent_event["payload"]["content"] == "This is the parent comment."
    assert "children" in parent_event, "Parent should have children field"
    assert len(parent_event["children"]) == 1, "Parent should have exactly 1 child"

    # Verify the child exists and has NO grandchildren
    child_event = parent_event["children"][0]
    assert child_event["id"] == child_comment_id
    assert child_event["payload"]["content"] == "This is a reply to the parent."
    assert child_event["parent_id"] == parent_comment_id

    # Child should have no children (grandchild was rejected)
    assert (
        "children" not in child_event or len(child_event.get("children", [])) == 0
    ), "Child should have no children (nested replies rejected)"

    # Step 5: Verify we can still create another direct reply to the parent using reply endpoint
    second_child_data = copy.deepcopy(events_resource_data)
    second_child_data["payload"]["content"] = "Another reply to parent."
    response = client.post(
        f"/requests/{request_id}/comments/{parent_comment_id}/reply",
        headers=headers,
        json=second_child_data,
    )
    assert (
        response.status_code == 201
    ), "Should be able to create another child of parent"
    assert response.json.get("parent_id") == parent_comment_id

    # Refresh and verify parent now has 2 children
    RequestEvent.index.refresh()
    response = client.get(f"/requests/{request_id}/timeline", headers=headers)
    top_level_hits = [
        hit for hit in response.json["hits"]["hits"] if not hit.get("parent_id")
    ]
    parent_event = top_level_hits[0]
    assert len(parent_event["children"]) == 2, "Parent should have 2 children now"


def test_get_replies_endpoint(
    app, client_logged_as, headers, events_resource_data, example_request
):
    """Test GET /comments/{comment_id}/replies endpoint for paginated replies."""
    client = client_logged_as("user1@example.org")
    request_id = example_request.id

    # Create a parent comment
    parent_data = copy.deepcopy(events_resource_data)
    parent_data["payload"]["content"] = "Parent comment"
    response = client.post(
        f"/requests/{request_id}/comments", headers=headers, json=parent_data
    )
    assert response.status_code == 201
    parent_comment_id = response.json["id"]

    # Create 3 child replies
    child_ids = []
    for i in range(3):
        child_data = copy.deepcopy(events_resource_data)
        child_data["payload"]["content"] = f"Reply {i + 1}"
        response = client.post(
            f"/requests/{request_id}/comments/{parent_comment_id}/reply",
            headers=headers,
            json=child_data,
        )
        assert response.status_code == 201
        child_ids.append(response.json["id"])

    # Refresh index
    RequestEvent.index.refresh()

    # Test GET /replies endpoint
    response = client.get(
        f"/requests/{request_id}/comments/{parent_comment_id}/replies",
        headers=headers,
    )
    assert response.status_code == 200
    assert "hits" in response.json
    hits = response.json["hits"]["hits"]
    assert len(hits) == 3, "Should return all 3 replies"

    # Verify content
    contents = [hit["payload"]["content"] for hit in hits]
    assert "Reply 1" in contents
    assert "Reply 2" in contents
    assert "Reply 3" in contents

    # Verify all have the correct parent_id
    for hit in hits:
        assert hit["parent_id"] == parent_comment_id

    # Test pagination - get first page with size=2
    response = client.get(
        f"/requests/{request_id}/comments/{parent_comment_id}/replies?size=2&page=1",
        headers=headers,
    )
    assert response.status_code == 200
    hits = response.json["hits"]["hits"]
    assert len(hits) == 2, "Should return 2 replies (page size)"

    # Test pagination - get second page
    response = client.get(
        f"/requests/{request_id}/comments/{parent_comment_id}/replies?size=2&page=2",
        headers=headers,
    )
    assert response.status_code == 200
    hits = response.json["hits"]["hits"]
    assert len(hits) == 1, "Should return 1 reply (remaining)"


def test_children_preview_limit(
    app, client_logged_as, headers, events_resource_data, example_request
):
    """Test that children respects the preview limit."""
    client = client_logged_as("user1@example.org")
    request_id = example_request.id

    # Create a parent comment
    parent_data = copy.deepcopy(events_resource_data)
    parent_data["payload"]["content"] = "Parent with many replies"
    response = client.post(
        f"/requests/{request_id}/comments", headers=headers, json=parent_data
    )
    assert response.status_code == 201
    parent_comment_id = response.json["id"]

    # Create 7 child replies (more than the default limit of 5)
    for i in range(7):
        child_data = copy.deepcopy(events_resource_data)
        child_data["payload"]["content"] = f"Reply number {i + 1}"
        response = client.post(
            f"/requests/{request_id}/comments/{parent_comment_id}/reply",
            headers=headers,
            json=child_data,
        )
        assert response.status_code == 201

    # Refresh index
    RequestEvent.index.refresh()

    # Get timeline and check parent's children
    response = client.get(f"/requests/{request_id}/timeline", headers=headers)
    assert response.status_code == 200
    hits = response.json["hits"]["hits"]
    parent_event = hits[0]

    # Verify preview limit is respected (default is 5)
    assert "children" in parent_event
    assert len(parent_event["children"]) == 5, "Should only show 5 children in preview"

    # Verify we can get all replies via the /replies endpoint
    response = client.get(
        f"/requests/{request_id}/comments/{parent_comment_id}/replies",
        headers=headers,
    )
    assert response.status_code == 200
    all_replies = response.json["hits"]["hits"]
    assert len(all_replies) == 7, "Replies endpoint should return all 7 replies"


def test_child_comment_permissions(
    app, client_logged_as, headers, events_resource_data, example_request
):
    """Test permissions on child comments for different users."""
    request_id = example_request.id

    # User 1 creates parent comment and submits request
    client = client_logged_as("user1@example.org")
    parent_data = copy.deepcopy(events_resource_data)
    parent_data["payload"]["content"] = "Parent by user1"
    response = client.post(
        f"/requests/{request_id}/comments", headers=headers, json=parent_data
    )
    assert response.status_code == 201
    parent_comment_id = response.json["id"]

    # User 1 submits the request
    response = client.post(f"/requests/{request_id}/actions/submit", headers=headers)
    assert response.status_code == 200

    # User 2 creates a reply
    client = client_logged_as("user2@example.org")
    reply_data = copy.deepcopy(events_resource_data)
    reply_data["payload"]["content"] = "Reply by user2"
    response = client.post(
        f"/requests/{request_id}/comments/{parent_comment_id}/reply",
        headers=headers,
        json=reply_data,
    )
    assert response.status_code == 201
    reply_id = response.json["id"]

    # Verify user2 can see their own reply
    assert response.json["permissions"]["can_update_comment"] is True
    assert response.json["permissions"]["can_delete_comment"] is True

    # User 1 tries to update user2's reply - should fail
    client = client_logged_as("user1@example.org")
    update_data = copy.deepcopy(events_resource_data)
    update_data["payload"]["content"] = "Trying to update user2's reply"
    response = client.put(
        f"/requests/{request_id}/comments/{reply_id}",
        headers=headers,
        json=update_data,
    )
    assert (
        response.status_code == 403
    ), "User1 should not be able to update user2's reply"

    # User 1 tries to delete user2's reply - should fail
    response = client.delete(
        f"/requests/{request_id}/comments/{reply_id}",
        headers=headers,
    )
    assert (
        response.status_code == 403
    ), "User1 should not be able to delete user2's reply"

    # Refresh index and verify permissions in timeline
    RequestEvent.index.refresh()
    response = client.get(f"/requests/{request_id}/timeline", headers=headers)
    assert response.status_code == 200
    hits = response.json["hits"]["hits"]
    parent_event = next((hit for hit in hits if hit["id"] == parent_comment_id), None)

    # Check permissions on child in children
    reply_in_preview = next(
        (c for c in parent_event["children"] if c["id"] == reply_id), None
    )
    assert reply_in_preview is not None
    assert reply_in_preview["permissions"]["can_update_comment"] is False
    assert reply_in_preview["permissions"]["can_delete_comment"] is False


def test_update_parent_with_children(
    app, client_logged_as, headers, events_resource_data, example_request
):
    """Test updating a parent comment that has child replies."""
    client = client_logged_as("user1@example.org")
    request_id = example_request.id

    # Create parent comment
    parent_data = copy.deepcopy(events_resource_data)
    parent_data["payload"]["content"] = "Original parent content"
    response = client.post(
        f"/requests/{request_id}/comments", headers=headers, json=parent_data
    )
    assert response.status_code == 201
    parent_comment_id = response.json["id"]

    # Create 2 child replies
    for i in range(2):
        child_data = copy.deepcopy(events_resource_data)
        child_data["payload"]["content"] = f"Child reply {i + 1}"
        response = client.post(
            f"/requests/{request_id}/comments/{parent_comment_id}/reply",
            headers=headers,
            json=child_data,
        )
        assert response.status_code == 201

    # Refresh index
    RequestEvent.index.refresh()

    # Update the parent comment
    updated_parent_data = copy.deepcopy(events_resource_data)
    updated_parent_data["payload"]["content"] = "Updated parent content"
    response = client.put(
        f"/requests/{request_id}/comments/{parent_comment_id}",
        headers=headers,
        json=updated_parent_data,
    )
    assert response.status_code == 200
    assert response.json["payload"]["content"] == "Updated parent content"

    # Refresh index and verify timeline
    RequestEvent.index.refresh()
    response = client.get(f"/requests/{request_id}/timeline", headers=headers)
    assert response.status_code == 200
    hits = response.json["hits"]["hits"]
    parent_event = hits[0]

    # Verify parent content is updated
    assert parent_event["payload"]["content"] == "Updated parent content"

    # Verify children are still present and unchanged
    assert len(parent_event["children"]) == 2

    # Verify child content is unchanged
    child_contents = [c["payload"]["content"] for c in parent_event["children"]]
    assert "Child reply 1" in child_contents
    assert "Child reply 2" in child_contents


def test_join_relationship_queries(
    app,
    client_logged_as,
    identity_simple,
    headers,
    events_resource_data,
    example_request,
):
    """Test OpenSearch join relationship queries for comment parent-child relationships.

    This test verifies the join relationship implementation works correctly:
    1. Join relationship field is set properly (comment/reply)
    2. has_child query with inner_hits works for timeline view
    3. parent_id query works for pagination
    """
    from invenio_requests.proxies import current_requests

    client = client_logged_as("user1@example.org")
    identity = identity_simple
    request_id = example_request.id

    # Step 1: Create a parent comment
    parent_data = copy.deepcopy(events_resource_data)
    parent_data["payload"]["content"] = "Parent comment for join test"
    response = client.post(
        f"/requests/{request_id}/comments", headers=headers, json=parent_data
    )
    assert response.status_code == 201
    parent_comment_id = response.json["id"]

    # Step 2: Create first child comment (reply)
    reply1_data = copy.deepcopy(events_resource_data)
    reply1_data["payload"]["content"] = "First reply for join test"
    response = client.post(
        f"/requests/{request_id}/comments/{parent_comment_id}/reply",
        headers=headers,
        json=reply1_data,
    )

    assert response.status_code == 201
    reply1_id = response.json["id"]

    # Step 3: Create second child comment (reply)
    reply2_data = copy.deepcopy(events_resource_data)
    reply2_data["payload"]["content"] = "Second reply for join test"
    response = client.post(
        f"/requests/{request_id}/comments/{parent_comment_id}/reply",
        headers=headers,
        json=reply2_data,
    )
    assert response.status_code == 201
    reply2_id = response.json["id"]

    # Step 4: Refresh index
    RequestEvent.index.refresh()

    # Step 5: Test timeline query with has_child + inner_hits
    # Use the service method directly for testing
    service = current_requests.request_events_service
    result = service.search(
        identity,
        request_id,
        preview_size=10,
    )

    # Verify results
    results_dict = result.to_dict()
    hits = results_dict["hits"]["hits"]

    # Should have 1 parent comment
    assert len(hits) >= 1

    # Find our parent comment
    parent_hit = next((hit for hit in hits if hit["id"] == parent_comment_id), None)
    assert parent_hit is not None

    # Verify children is present and contains 2 children
    assert "children" in parent_hit
    assert len(parent_hit["children"]) == 2

    # Verify children content
    child_contents = [c["payload"]["content"] for c in parent_hit["children"]]
    assert "First reply for join test" in child_contents
    assert "Second reply for join test" in child_contents

    # Step 6: Test pagination with parent_id query
    result = service.get_comment_replies(
        identity,
        parent_comment_id,
        params={"size": 1, "page": 1},  # Get 1 child per page
    )

    # Verify first page
    results_dict = result.to_dict()
    hits = results_dict["hits"]["hits"]
    assert len(hits) == 1
    assert hits[0]["payload"]["content"] in [
        "First reply for join test",
        "Second reply for join test",
    ]

    # Get second page
    result = service.get_comment_replies(
        identity,
        parent_comment_id,
        params={"size": 1, "page": 2},
    )

    results_dict = result.to_dict()
    hits = results_dict["hits"]["hits"]
    assert len(hits) == 1
    assert hits[0]["payload"]["content"] in [
        "First reply for join test",
        "Second reply for join test",
    ]

    # Step 7: Update a child and verify join queries still work
    updated_reply_data = copy.deepcopy(events_resource_data)
    updated_reply_data["payload"]["content"] = "Updated first reply for join test"
    response = client.put(
        f"/requests/{request_id}/comments/{reply1_id}",
        headers=headers,
        json=updated_reply_data,
    )
    assert response.status_code == 200

    # Refresh index
    RequestEvent.index.refresh()

    # Verify has_child query sees the update
    result = service.search(
        identity,
        request_id,
        preview_size=10,
    )

    results_dict = result.to_dict()
    hits = results_dict["hits"]["hits"]
    parent_hit = next((hit for hit in hits if hit["id"] == parent_comment_id), None)
    assert parent_hit is not None

    # Find updated child in inner_hits
    updated_child = next(
        (c for c in parent_hit["children"] if c["id"] == reply1_id),
        None,
    )
    assert updated_child is not None
    assert updated_child["payload"]["content"] == "Updated first reply for join test"

    # Verify parent_id query also sees the update
    result = service.get_comment_replies(
        identity,
        parent_comment_id,
        params={"size": 10},
    )

    results_dict = result.to_dict()
    child_contents = [hit["payload"]["content"] for hit in results_dict["hits"]["hits"]]
    assert "Updated first reply for join test" in child_contents
