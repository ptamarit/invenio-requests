# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Request Files resource tests."""

import re
from io import BytesIO

import pytest

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


def test_simple_files_flow(app, client_logged_as, example_request, headers, location):
    # Passing the `location` fixture to make sure that a default bucket location is defined.
    assert location.default == True

    request_id = example_request.id
    # key = "filename.ext"
    # data = BytesIO(b"test file content")
    key = "screenshot.png"
    data_content = b"\x89PNG\r\n\x1a\n"
    data = BytesIO(data_content)

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
        "metadata": {"original_filename": "screenshot.png"},
        "checksum": "md5:e9dd2797018cad79186e03e8c5aec8dc",
        "size": 8,
        "mimetype": "image/png",
        "links": {
            "self": f"/api/requests/{request_id}/files/{unique_key}",
            "content": f"/api/requests/{request_id}/files/{unique_key}/content",
            "commit": f"/api/requests/{request_id}/files/{unique_key}/commit",
            "download_html": f"/requests/{request_id}/files/{unique_key}",
        },
    }
    assert expected_json == response.json

    # Submit comment.
    response = client.post(f"/requests/{request_id}/comments", headers=headers, json=events_resource_data_with_files)
    expected_data = [unique_key]
    # assert_api_response(response, 200, expected_data)

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
