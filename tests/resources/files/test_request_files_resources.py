# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Request Files resource tests."""

import hashlib
import re
from io import BytesIO
from uuid import UUID


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


def upload_file(
    client,
    request_id,
    key_base,
    key_ext,
    data_content,
    headers_upload,
    expected_status_code=200,
    expected_json=None,
):
    # Upload a file.
    response = client.put(
        f"/requests/{request_id}/files/upload/{key_base}{key_ext}",
        headers=headers_upload,
        data=BytesIO(data_content),
    )

    assert expected_status_code == response.status_code

    if expected_status_code != 200 and expected_json is not None:
        assert expected_json == response.json
    else:
        assert "id" in response.json
        id_ = response.json["id"]

        # Validate that id_ is a valid UUID.
        UUID(id_)

        # Validate that the key has a base32 suffix (length of 10 characters, split every 5 characters)
        assert "key" in response.json
        unique_key = response.json["key"]
        assert re.match(key_base + "-\w{5}-\w{5}" + key_ext, unique_key)

        key = f"{key_base}{key_ext}"
        size = len(data_content)
        mimetype = "image/png" if key_ext == ".png" else "application/pdf"

        expected_json = {
            "id": id_,
            "key": unique_key,
            "metadata": {"original_filename": key},
            "checksum": f"md5:{hashlib.md5(data_content).hexdigest()}",
            "size": size,
            "mimetype": mimetype,
            "links": {
                "self": f"https://127.0.0.1:5000/api/requests/{request_id}/files/{unique_key}",
                "content": f"https://127.0.0.1:5000/api/requests/{request_id}/files/{unique_key}/content",
                "download_html": f"https://127.0.0.1:5000/requests/{request_id}/files/{unique_key}",
            },
        }

        return {
            "key": unique_key,
        }


def delete_file(
    client,
    request_id,
    key,
    headers,
    expected_status_code=204,
    expected_json=None,
):
    # Delete the file.
    response = client.delete(
        f"/requests/{request_id}/files/{key}",
        headers=headers,
    )
    assert expected_status_code == response.status_code
    assert expected_json == response.json


def read_file(
    client,
    request_id,
    key,
    data_content,
    headers,
    expected_status_code=200,
    expected_json=None,
):
    # Read the file.
    response = client.get(
        f"/requests/{request_id}/files/{key}/content",
        headers=headers,
    )
    assert expected_status_code == response.status_code

    if expected_status_code != 200 and expected_json is not None:
        assert expected_json == response.json
    else:
        assert data_content == response.data


def test_file_upload_delete_read(
    app,
    client_logged_as,
    example_request,
    headers,
    headers_upload,
    location,
):
    # Passing the `location` fixture to make sure that a default bucket location is defined.
    assert location.default == True

    request_id = example_request.id

    file1_key_base = "screenshot"
    file1_key_ext = ".png"
    file1_data_content = b"\x89PNG\r\n\x1a\n ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    file2_key_base = "report"
    file2_key_ext = ".pdf"
    file2_data_content = b"%PDF ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    file3_key_base = "big"
    file3_key_ext = ".dat"
    # 11 MB file
    file3_data_content = b"1234567890A" * 1000 * 1000

    client = client_logged_as("user1@example.org")

    # Upload first file
    file1_details = upload_file(
        client=client,
        request_id=request_id,
        key_base=file1_key_base,
        key_ext=file1_key_ext,
        data_content=file1_data_content,
        headers_upload=headers_upload,
    )

    # Upload second file
    file2_details = upload_file(
        client=client,
        request_id=request_id,
        key_base=file2_key_base,
        key_ext=file2_key_ext,
        data_content=file2_data_content,
        headers_upload=headers_upload,
    )

    # Upload third file -> Failure
    upload_file(
        client=client,
        request_id=request_id,
        key_base=file3_key_base,
        key_ext=file3_key_ext,
        data_content=file3_data_content,
        headers_upload=headers_upload,
        expected_status_code=400,
        expected_json={"message": "File size exceeds limit", "status": 400},
    )

    # Verify first file
    read_file(
        client=client,
        request_id=request_id,
        key=file1_details["key"],
        data_content=file1_data_content,
        headers=headers,
    )

    # Verify second file
    read_file(
        client=client,
        request_id=request_id,
        key=file2_details["key"],
        data_content=file2_data_content,
        headers=headers,
    )

    # Delete first file
    delete_file(
        client=client,
        request_id=request_id,
        key=file1_details["key"],
        headers=headers,
    )

    # Verify that the first file is not present anymore
    read_file(
        client=client,
        request_id=request_id,
        key=file1_details["key"],
        data_content=file1_data_content,
        headers=headers,
        expected_status_code=404,
        expected_json={"message": "File not found", "status": 404},
    )

    # Delete first file again -> Failure
    delete_file(
        client=client,
        request_id=request_id,
        key=file1_details["key"],
        headers=headers,
        expected_status_code=404,
        expected_json={"message": "File not found", "status": 404},
    )
