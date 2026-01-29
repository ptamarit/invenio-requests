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
from uuid import UUID

from invenio_requests.customizations.event_types import CommentEventType
from invenio_requests.records.api import RequestEvent


def assert_api_response_json(expected_json, received_json):
    """Assert the REST API response's json."""
    # We don't compare dynamic times at this point
    received_json.pop("created", None)
    received_json.pop("updated", None)
    for file in received_json.get("payload", {}).get("files", []):
        file.pop("created")
    for hits in received_json.get("hits", {}).get("hits", []):
        hits.pop("created")
        hits.pop("updated")
        for file in hits.get("payload", {}).get("files", []):
            file.pop("created")
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
            "file_id": id_,
            "key": unique_key,
            "original_filename": key,
            "size": size,
            "mimetype": mimetype,
            "links": {
                "self": f"/api/requests/{request_id}/files/{unique_key}",
                "content": f"/api/requests/{request_id}/files/{unique_key}/content",
                "download_html": f"/requests/{request_id}/files/{unique_key}",
            },
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


def get_events_resource_data_with_files(files_details, events_resource_data):
    events_resource_data_with_files = copy.deepcopy(events_resource_data)
    if files_details:
        events_resource_data_with_files["payload"]["files"] = [
            {"file_id": file_details["file_id"]} for file_details in files_details
        ]
    return events_resource_data_with_files


def get_and_assert_timeline_response(
    client,
    request_id,
    comment_id,
    files_details,
    events_resource_data,
    headers,
    expected_revision_id,
):
    # Refresh index
    RequestEvent.index.refresh()

    # Get the timeline.
    response = client.get(
        f"/requests/{request_id}/timeline?expand=1",
        headers=headers,
    )

    expected_status_code = 200

    expected_json = {
        "hits": {
            "hits": [
                {
                    "children": [],
                    "children_count": 0,
                    "created_by": {
                        "user": "1",
                    },
                    "expanded": {
                        "created_by": {
                            "active": True,
                            "blocked_at": None,
                            "confirmed_at": None,
                            "email": "user1@example.org",
                            "id": "1",
                            "is_current_user": True,
                            "links": {
                                "avatar": "https://127.0.0.1:5000/api/users/1/avatar.svg",
                                "records_html": "https://127.0.0.1:5000/search/records?q=parent.access.owned_by.user:1",
                                "self": "https://127.0.0.1:5000/api/users/1",
                            },
                            "profile": {
                                "affiliations": "CERN",
                                "full_name": "user1",
                            },
                            "username": None,
                            "verified_at": None,
                        },
                    },
                    "id": comment_id,
                    "links": {
                        "replies": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}/replies",
                        "reply": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}/reply",
                        "self": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}",
                        "self_html": f"https://127.0.0.1:5000/requests/{request_id}#commentevent-{comment_id}",
                    },
                    "parent_id": None,
                    "payload": {
                        "content": events_resource_data["payload"]["content"],
                        "format": events_resource_data["payload"]["format"],
                        "files": files_details,
                    },
                    "permissions": {
                        "can_delete_comment": True,
                        "can_reply_comment": True,
                        "can_update_comment": True,
                    },
                    "revision_id": expected_revision_id,
                    "type": "C",
                },
            ],
            "total": 1,
        },
        "links": {
            "self": f"https://127.0.0.1:5000/api/requests/{request_id}/timeline?expand=True&page=1&size=25&sort=oldest",
        },
        "page": 1,
        "sortBy": "oldest",
    }
    if not files_details:
        expected_json["hits"]["hits"][0]["payload"].pop("files")

    assert_api_response(response, expected_status_code, expected_json)


def assert_comment_response(
    expected_status_code,
    expected_revision_id,
    response,
    request_id,
    comment_id,
    files_details,
    events_resource_data_with_files,
):
    expected_json = {
        "id": comment_id,
        "payload": {
            "content": events_resource_data_with_files["payload"]["content"],
            "format": events_resource_data_with_files["payload"]["format"],
            "files": files_details,
        },
        "created_by": {"user": "1"},
        "links": {
            "reply": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}/reply",
            "replies": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}/replies",
            "self": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}",
            "self_html": f"https://127.0.0.1:5000/requests/{request_id}#commentevent-{comment_id}",
        },
        "parent_id": None,
        "permissions": {
            "can_update_comment": True,
            "can_delete_comment": True,
            "can_reply_comment": True,
        },
        "revision_id": expected_revision_id,
        "type": CommentEventType.type_id,
    }
    if not files_details:
        expected_json["payload"].pop("files")
    assert_api_response(response, expected_status_code, expected_json)


def submit_comment(
    client,
    request_id,
    files_details,
    events_resource_data,
    headers,
    expected_status_code=201,
    expected_json=None,
):
    events_resource_data_with_files = get_events_resource_data_with_files(
        files_details=files_details,
        events_resource_data=events_resource_data,
    )

    response = client.post(
        f"/requests/{request_id}/comments",
        headers=headers,
        json=events_resource_data_with_files,
    )

    assert expected_status_code == response.status_code

    if expected_status_code != 201 and expected_json is not None:
        assert expected_json == response.json
    else:
        comment_id = response.json["id"]

        assert_comment_response(
            expected_status_code=expected_status_code,
            expected_revision_id=1,
            response=response,
            request_id=request_id,
            comment_id=comment_id,
            files_details=files_details,
            events_resource_data_with_files=events_resource_data_with_files,
        )

        get_and_assert_timeline_response(
            client=client,
            request_id=request_id,
            comment_id=comment_id,
            files_details=files_details,
            events_resource_data=events_resource_data,
            headers=headers,
            expected_revision_id=1,
        )

        return comment_id


def update_comment(
    client,
    request_id,
    comment_id,
    files_details,
    events_resource_data,
    headers,
):
    events_resource_data_with_files = get_events_resource_data_with_files(
        files_details=files_details,
        events_resource_data=events_resource_data,
    )

    response = client.put(
        f"/requests/{request_id}/comments/{comment_id}",
        headers=headers,
        json=events_resource_data_with_files,
    )

    assert_comment_response(
        expected_status_code=200,
        expected_revision_id=2,
        response=response,
        request_id=request_id,
        comment_id=comment_id,
        files_details=files_details,
        events_resource_data_with_files=events_resource_data_with_files,
    )

    get_and_assert_timeline_response(
        client=client,
        request_id=request_id,
        comment_id=comment_id,
        files_details=files_details,
        events_resource_data=events_resource_data,
        headers=headers,
        expected_revision_id=2,
    )


def delete_comment(
    client,
    request_id,
    comment_id,
    headers,
):
    # Delete the file
    response = client.delete(
        f"/requests/{request_id}/comments/{comment_id}",
        headers=headers,
    )

    assert 204 == response.status_code
    assert None == response.json


def test_update_comment_to_remove_files(
    app,
    client_logged_as,
    example_request,
    headers,
    headers_upload,
    location,
    events_resource_data,
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

    # Submit comment with file references (only successful uploads)
    comment_id = submit_comment(
        client=client,
        request_id=request_id,
        # file3 not included
        files_details=[file1_details, file2_details],
        events_resource_data=events_resource_data,
        headers=headers,
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

    # Update comment with reduced files array
    update_comment(
        client=client,
        request_id=request_id,
        comment_id=comment_id,
        # Only second file remains
        files_details=[file2_details],
        events_resource_data=events_resource_data,
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

    # Verify that the second file is still present
    read_file(
        client=client,
        request_id=request_id,
        key=file2_details["key"],
        data_content=file2_data_content,
        headers=headers,
    )


def test_update_comment_to_add_files(
    app,
    client_logged_as,
    example_request,
    headers,
    headers_upload,
    location,
    events_resource_data,
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

    client = client_logged_as("user1@example.org")

    # Submit a comment without files
    comment_id = submit_comment(
        client=client,
        request_id=request_id,
        files_details=[],
        events_resource_data=events_resource_data,
        headers=headers,
    )

    # Upload new files
    file1_details = upload_file(
        client=client,
        request_id=request_id,
        key_base=file1_key_base,
        key_ext=file1_key_ext,
        data_content=file1_data_content,
        headers_upload=headers_upload,
    )

    file2_details = upload_file(
        client=client,
        request_id=request_id,
        key_base=file2_key_base,
        key_ext=file2_key_ext,
        data_content=file2_data_content,
        headers_upload=headers_upload,
    )

    # Update comment with new content and files
    update_comment(
        client=client,
        request_id=request_id,
        comment_id=comment_id,
        files_details=[file1_details, file2_details],
        events_resource_data=events_resource_data,
        headers=headers,
    )

    # Verify that both files are present
    read_file(
        client=client,
        request_id=request_id,
        key=file1_details["key"],
        data_content=file1_data_content,
        headers=headers,
    )

    read_file(
        client=client,
        request_id=request_id,
        key=file2_details["key"],
        data_content=file2_data_content,
        headers=headers,
    )


def test_file_deleted_between_upload_and_submit(
    app,
    client_logged_as,
    example_request,
    headers,
    headers_upload,
    location,
    events_resource_data,
):
    # Passing the `location` fixture to make sure that a default bucket location is defined.
    assert location.default == True

    request_id = example_request.id

    file1_key_base = "screenshot"
    file1_key_ext = ".png"
    file1_data_content = b"\x89PNG\r\n\x1a\n ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    # Upload
    client = client_logged_as("user1@example.org")
    file1_details = upload_file(
        client=client,
        request_id=request_id,
        key_base=file1_key_base,
        key_ext=file1_key_ext,
        data_content=file1_data_content,
        headers_upload=headers_upload,
    )

    # Admin deletes file
    client = client_logged_as("admin@example.org")
    delete_file(
        client=client,
        request_id=request_id,
        key=file1_details["key"],
        headers=headers,
    )

    # Deleting the file again should fail
    delete_file(
        client=client,
        request_id=request_id,
        key=file1_details["key"],
        headers=headers,
        expected_status_code=404,
        expected_json={"message": "File not found", "status": 404},
    )

    # Verify that the file is not present anymore
    read_file(
        client=client,
        request_id=request_id,
        key=file1_details["key"],
        data_content=file1_data_content,
        headers=headers,
        expected_status_code=404,
        expected_json={"message": "File not found", "status": 404},
    )

    # User submits
    client = client_logged_as("user1@example.org")
    file1_id = file1_details["file_id"]
    submit_comment(
        client=client,
        request_id=request_id,
        files_details=[file1_details],
        events_resource_data=events_resource_data,
        headers=headers,
        expected_status_code=400,
        expected_json={
            "message": "A validation error occurred.",
            "status": 400,
            "errors": [
                {
                    "field": "payload.files[0]",
                    "messages": [f"File {file1_id} not found."],
                },
            ],
        },
    )


def test_delete_comment_with_files(
    app,
    client_logged_as,
    example_request,
    headers,
    headers_upload,
    location,
    events_resource_data,
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

    # Submit comment with file references
    comment_id = submit_comment(
        client=client,
        request_id=request_id,
        files_details=[file1_details, file2_details],
        events_resource_data=events_resource_data,
        headers=headers,
    )

    # Delete the comment
    delete_comment(
        client=client,
        request_id=request_id,
        comment_id=comment_id,
        headers=headers,
    )

    # Verify that the files are not present anymore
    read_file(
        client=client,
        request_id=request_id,
        key=file1_details["key"],
        data_content=file1_data_content,
        headers=headers,
        expected_status_code=404,
        expected_json={"message": "File not found", "status": 404},
    )

    read_file(
        client=client,
        request_id=request_id,
        key=file2_details["key"],
        data_content=file2_data_content,
        headers=headers,
        expected_status_code=404,
        expected_json={"message": "File not found", "status": 404},
    )
