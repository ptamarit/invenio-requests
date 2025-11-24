# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Request Files resource tests."""

import copy
from io import BytesIO


# TODO: This is duplicated code.
def assert_api_response_json(expected_json, received_json):
    """Assert the REST API response's json."""
    # We don't compare dynamic times at this point
    # received_json.pop("created")
    # received_json.pop("updated")
    # received_json.pop("revision_id")
    assert expected_json == received_json


def assert_api_response(response, code, json):
    """Assert the REST API response."""
    assert code == response.status_code
    assert_api_response_json(json, response.json)


def test_simple_files_flow(app, client_logged_as, example_request):
    request_id = example_request.id
    # key = "filename.ext"
    # data = BytesIO(b"test file content")
    key = "screenshot.png"
    data = BytesIO(b"\x89PNG\r\n\x1a\n")

    headers_binary = {
        # TODO: Use image/png instead of  a generic one?
        "content-type": "application/octet-stream",
        "accept": "application/json",
    }

    client = client_logged_as("user1@example.org")
    response = client.put(
        f"/api/requests/{request_id}/files/upload/{key}",
        headers=headers_binary,
        data=data,
    )

    expected_data = {
        # TODO: Use example_request.number ?
        "id": "f9e8d7c6-b5a4-3210-9876-543210fedcba",
        "key": "a1b2c3d4-e5f6-7890-abcd-ef1234567890-screenshot.png",
        "metadata": {"original_filename": "screenshot.png"},
        "checksum": "md5:d41d8cd98f00b204e9800998ecf8427e",
        "size": 45678,
        "mimetype": "image/png",
        "links": {
            "self": "/api/requests/{request_id}/files/{key}",
            "content": "/api/requests/{request_id}/files/{key}/content",
            "commit": "/api/requests/{request_id}/files/{key}/commit",
            "download_html": "/requests/{request_id}/files/{key}",
        },
    }
    assert_api_response(response, 200, expected_data)

    # submit the request
    url = response.json["links"]["actions"]["submit"]
    response = client.post(url[len("https://127.0.0.1:5000/api") :], headers=headers)
    expected_data.update(
        {
            "status": "submitted",
            "is_open": True,
            "links": {
                "self": f"https://127.0.0.1:5000/api/requests/{id_}",
                "self_html": f"https://127.0.0.1:5000/requests/{id_}",
                "timeline": f"https://127.0.0.1:5000/api/requests/{id_}/timeline",
                "comments": f"https://127.0.0.1:5000/api/requests/{id_}/comments",
                "actions": {
                    "cancel": f"https://127.0.0.1:5000/api/requests/{id_}/actions/cancel",  # noqa
                },
            },
            "last_activity_at": response.json["updated"],
        }
    )
    assert_api_response(response, 200, expected_data)

    # cancel the request
    url = response.json["links"]["actions"]["cancel"]
    response = client.post(url[len("https://127.0.0.1:5000/api") :], headers=headers)
    expected_data.update(
        {
            "status": "cancelled",
            "is_closed": True,
            "is_open": False,
            "links": {
                "self": f"https://127.0.0.1:5000/api/requests/{id_}",
                "self_html": f"https://127.0.0.1:5000/requests/{id_}",
                "timeline": f"https://127.0.0.1:5000/api/requests/{id_}/timeline",
                "comments": f"https://127.0.0.1:5000/api/requests/{id_}/comments",
                "actions": {},
            },
            "last_activity_at": response.json["updated"],
        }
    )
    assert_api_response(response, 200, expected_data)

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
