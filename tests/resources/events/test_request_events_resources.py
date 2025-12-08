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
            "self": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}",  # noqa
            "self_html": f"https://127.0.0.1:5000/requests/{request_id}#commentevent-{comment_id}",
            # "report": ""  # TODO
        },
        "permissions": {"can_update_comment": True, "can_delete_comment": True},
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
            "self": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}",  # noqa
            "self_html": f"https://127.0.0.1:5000/requests/{request_id}#commentevent-{comment_id}",
            # "report": ""  # TODO
        },
        "permissions": {"can_update_comment": True, "can_delete_comment": True},
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
    # User 2 cannot updated or delete the comment created by user 1
    expected_json_1["permissions"] = {
        "can_update_comment": False,
        "can_delete_comment": False,
    }
    assert_api_response_json(expected_json_1, response.json["hits"]["hits"][0])
    expected_json_3 = {
        "created_by": {"user": "2"},
        "revision_id": 1,
        "payload": {
            "content": "deleted a comment",
            "format": "html",
            "event": "comment_deleted",
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
