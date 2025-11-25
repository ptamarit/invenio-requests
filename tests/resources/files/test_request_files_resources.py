# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Request Files resource tests."""

from io import BytesIO

import pytest


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


def test_simple_files_flow(app, client_logged_as, example_request, location):
    # Passing the `location` fixture to make sure that a default bucket location is defined.
    assert location.default == True

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

    # Upload a file.
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
        "checksum": "md5:e9dd2797018cad79186e03e8c5aec8dc",
        "size": 8,
        "mimetype": "image/png",
        "links": {
            "self": "/api/requests/{request_id}/files/{key}",
            "content": "/api/requests/{request_id}/files/{key}/content",
            "download_html": "/requests/{request_id}/files/{key}",
        },
    }
    # assert_api_response(response, 200, expected_data) # TODO: Enable

    # TODO: They key should have a UUID.
    key_with_uuid = f"{key}"

    # Delete the file.
    response = client.delete(
        f"/api/requests/{request_id}/files/{key_with_uuid}",
        headers=headers_binary,
        data=data,
    )
    expected_data = None
    assert_api_response(response, 204, expected_data)

    # Delete the file again should fail
    with pytest.raises(FileNotFoundError):
        client.delete(
            f"/api/requests/{request_id}/files/{key_with_uuid}",
            headers=headers_binary,
            data=data,
        )

    # <img src="/requests/{id}/files/uuid-screenshot.png"

    # Retrieve file content (API endpoint)
    # GET /api/requests/{id}/files/{file_key}/content
    # <img src="/requests/{id}/files/{file_key}"
