# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Request Files resource tests."""

import copy
import hashlib
import re
from io import BytesIO

import pytest

from invenio_requests.customizations.event_types import CommentEventType

# TODO: This is duplicated code.
# def assert_api_response_json(expected_json, received_json):
#     """Assert the REST API response's json."""
#     # We don't compare dynamic times at this point
#     # received_json.pop("created")
#     # received_json.pop("updated")
#     # received_json.pop("revision_id")
#     assert expected_json == received_json


# def assert_api_response(response, code, json):
#     """Assert the REST API response."""
#     assert code == response.status_code
#     assert_api_response_json(json, response.json)


# tests/resources/events/test_request_events_resources.py::test_simple_comment_flow
# tests/resources/events/test_request_events_resources.py::test_timeline_links
# tests/resources/events/test_request_events_resources.py::test_empty_comment


def assert_api_response_json(expected_json, received_json):
    """Assert the REST API response's json."""
    # We don't compare dynamic times at this point
    received_json.pop("created")
    received_json.pop("updated")
    for file in received_json.get("payload", {}).get("files", []):
        file.pop("created")
    assert expected_json == received_json


def assert_api_response(response, code, json):
    """Assert the REST API response."""
    assert code == response.status_code
    assert_api_response_json(json, response.json)


def test_simple_files_flow(
    app,
    client_logged_as,
    example_request,
    headers,
    location,
    events_resource_data_with_empty_files,
):
    # Passing the `location` fixture to make sure that a default bucket location is defined.
    assert location.default == True

    request_id = example_request.id
    # key = "filename.ext"
    # data = BytesIO(b"test file content")
    key = "screenshot.png"
    data_content = b"\x89PNG\r\n\x1a\n"
    data = BytesIO(data_content)
    mimetype = "image/png"
    size = len(data_content)
    md5 = f"md5:{hashlib.md5(data_content).hexdigest()}"

    headers_binary = {
        "content-type": "application/octet-stream",
        "accept": "application/json",
    }

    client = client_logged_as("user1@example.org")

    # Upload a file.
    response = client.put(
        f"/requests/{request_id}/files/upload/{key}",
        headers=headers_binary,
        data=data,
    )

    assert 200 == response.status_code

    assert "id" in response.json
    id_ = response.json["id"]
    # TODO: Validate that id_ is a valid UUID?

    assert "key" in response.json
    unique_key = response.json["key"]
    assert re.match("screenshot-\w{5}-\w{5}.png", unique_key)

    expected_json = {
        "id": id_,
        "key": unique_key,
        "metadata": {"original_filename": key},
        "checksum": md5,
        "size": size,
        "mimetype": mimetype,
        "links": {
            "self": f"/api/requests/{request_id}/files/{unique_key}",
            "content": f"/api/requests/{request_id}/files/{unique_key}/content",
            "commit": f"/api/requests/{request_id}/files/{unique_key}/commit",
            "download_html": f"/requests/{request_id}/files/{unique_key}",
        },
    }
    assert expected_json == response.json

    # Submit comment with reference to file.
    events_resource_data_with_files = copy.deepcopy(
        events_resource_data_with_empty_files
    )
    events_resource_data_with_files["payload"]["files"] = [{"file_id": id_}]
    response = client.post(
        f"/requests/{request_id}/comments",
        headers=headers,
        json=events_resource_data_with_files,
    )

    comment_id = response.json["id"]
    expected_json = {
        "payload": {
            "content": events_resource_data_with_files["payload"]["content"],
            "format": events_resource_data_with_files["payload"]["format"],
            "files": [
                {
                    "file_id": id_,
                    "key": unique_key,
                    "original_filename": key,
                    "size": size,
                    "mimetype": mimetype,
                    # "created" not compared
                }
            ],
        },
        "created_by": {"user": "1"},
        "id": comment_id,
        "links": {
            "reply": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}/reply",  # noqa
            "replies": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}/replies",  # noqa
            "self": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}",  # noqa
            "self_html": f"https://127.0.0.1:5000/requests/{request_id}#commentevent-{comment_id}",
        },
        "parent_id": None,
        "permissions": {"can_update_comment": True, "can_delete_comment": True},
        "revision_id": 1,
        "type": CommentEventType.type_id,
    }
    assert_api_response(response, 201, expected_json)

    # {
    # "payload": {
    #     "content": "<p>I've completed my review...</p><p><a href=\"...\">reviewed_manuscript.pdf</a></p><p>Additionally, Figure 3 has a rendering issue:</p><img src=\"...\" />",
    #     "format": "html",
    #     "files": [
    #     {"file_id": "f1e2d3c4-e5f6-7890-abcd-ef1234567890"},
    #     {"file_id": "a2b3c4d5-e6f7-8901-bcde-f234567890ab"}
    #     ]
    # }
    # }

    # # List files.
    # response = client.get(
    #     f"/requests/{request_id}/files",
    #     headers=headers,
    #     data=data,
    # )
    # expected_data = [unique_key]
    # assert_api_response(response, 200, expected_data)

    # Access the file.
    response = client.get(
        f"/requests/{request_id}/files/{unique_key}/content",
        headers=headers,
        data=data,
    )
    assert 200 == response.status_code
    assert data_content == response.data

    #

    # TODO: Save a comment with file reference
    # TODO: Get the list of comments

    # Delete the file.
    response = client.delete(
        f"/requests/{request_id}/files/{unique_key}",
        headers=headers,
        data=data,
    )
    assert 204 == response.status_code
    assert None == response.json

    # TODO: Assert access rights here?

    # # List files.
    # response = client.get(
    #     f"/requests/{request_id}/files",
    #     headers=headers,
    #     data=data,
    # )
    # expected_data = []
    # assert_api_response(response, 200, expected_data)

    # Delete the file again should fail
    with pytest.raises(FileNotFoundError):
        client.delete(
            f"/requests/{request_id}/files/{unique_key}",
            headers=headers,
            data=data,
        )

    # No API endpoint here
    # <img src="/requests/{id}/files/uuid-screenshot.png"
    # <img src="/requests/{id}/files/{file_key}"

    # Retrieve file content (API endpoint)
    # GET /requests/{id}/files/{file_key}/content
