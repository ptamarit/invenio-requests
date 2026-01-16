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

# tests/resources/events/test_request_events_resources.py::test_simple_comment_flow
# tests/resources/events/test_request_events_resources.py::test_timeline_links
# tests/resources/events/test_request_events_resources.py::test_empty_comment


# # List files.
# response = client.get(
#     f"/requests/{request_id}/files",
#     headers=headers,
#     data=data,
# )
# expected_data = [unique_key]
# assert_api_response(response, 200, expected_data)

# TODO: Get the list of comments

# No API endpoint here
# <img src="/requests/{id}/files/uuid-screenshot.png"
# <img src="/requests/{id}/files/{file_key}"

# Retrieve file content (API endpoint)
# GET /requests/{id}/files/{file_key}/content


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
        # TODO: Validate that id_ is a valid UUID?

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
                "self": f"/api/requests/{request_id}/files/{unique_key}",
                "content": f"/api/requests/{request_id}/files/{unique_key}/content",
                # "commit": f"/api/requests/{request_id}/files/{unique_key}/commit",
                "download_html": f"/requests/{request_id}/files/{unique_key}",
            },
        }

        return {
            "file_id": id_,
            "key": unique_key,
            "original_filename": key,
            "size": size,
            "mimetype": mimetype,
            # TODO: Switch to download_html once the non-API URL works.
            "content": f"/api/requests/{request_id}/files/{unique_key}/content",
        }


def delete_file(
    client,
    request_id,
    key,
    headers,
):
    # Delete the file
    response = client.delete(
        f"/requests/{request_id}/files/{key}",
        headers=headers,
    )
    assert 204 == response.status_code
    assert None == response.json

    # TODO: Assert access rights here?


def access_file_content(client, request_id, key, data_content, headers):
    # Access the file.
    response = client.get(
        f"/requests/{request_id}/files/{key}/content",
        headers=headers,
    )
    assert 200 == response.status_code
    assert data_content == response.data


def get_events_resource_data_with_files(
    files_details, events_resource_data_with_empty_files
):
    events_resource_data_with_files = copy.deepcopy(
        events_resource_data_with_empty_files
    )
    events_resource_data_with_files["payload"]["files"] = [
        {"file_id": file_details["file_id"]} for file_details in files_details
    ]
    return events_resource_data_with_files


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
            "reply": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}/reply",  # noqa
            "replies": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}/replies",  # noqa
            "self": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}",  # noqa
            "self_html": f"https://127.0.0.1:5000/requests/{request_id}#commentevent-{comment_id}",
        },
        "parent_id": None,
        "permissions": {"can_update_comment": True, "can_delete_comment": True},
        "revision_id": expected_revision_id,
        "type": CommentEventType.type_id,
    }
    assert_api_response(response, expected_status_code, expected_json)


def submit_comment(
    client, request_id, files_details, events_resource_data_with_empty_files, headers
):
    events_resource_data_with_files = get_events_resource_data_with_files(
        files_details=files_details,
        events_resource_data_with_empty_files=events_resource_data_with_empty_files,
    )

    response = client.post(
        f"/requests/{request_id}/comments",
        headers=headers,
        json=events_resource_data_with_files,
    )

    comment_id = response.json["id"]

    assert_comment_response(
        expected_status_code=201,
        expected_revision_id=1,
        response=response,
        request_id=request_id,
        comment_id=comment_id,
        files_details=files_details,
        events_resource_data_with_files=events_resource_data_with_files,
    )

    # Backend validation: Checks that both file IDs exist in request bucket before accepting comment.

    return comment_id


def update_comment(
    client,
    request_id,
    comment_id,
    files_details,
    events_resource_data_with_empty_files,
    headers,
):
    events_resource_data_with_files = get_events_resource_data_with_files(
        files_details=files_details,
        events_resource_data_with_empty_files=events_resource_data_with_empty_files,
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

    # Critical requirement: Backend must allow payload.files array to be updated (not just content and format).


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

    # TODO: Assert access rights here?


def test_scenario_1_scenario_3_scenario_4(
    app,
    client_logged_as,
    example_request,
    headers,
    headers_upload,
    location,
    events_resource_data_with_empty_files,
):
    # Scenario 1: New Comment with Attachments

    # User actions:
    # 1. User starts typing “See attached files” in rich editor
    # 2. User selects 2 PDF files to attach
    # 3. Frontend uploads files (both complete successfully)
    # 4. User clicks “Submit comment”

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
    file3_key_ext = ".pdf"
    # 11 MB file
    file3_data_content = b"1234567890A" * 1000 * 1000

    client = client_logged_as("user1@example.org")

    # Step 1: Upload first file
    file1_details = upload_file(
        client=client,
        request_id=request_id,
        key_base=file1_key_base,
        key_ext=file1_key_ext,
        data_content=file1_data_content,
        headers_upload=headers_upload,
    )

    # Step 2: Upload second file
    file2_details = upload_file(
        client=client,
        request_id=request_id,
        key_base=file2_key_base,
        key_ext=file2_key_ext,
        data_content=file2_data_content,
        headers_upload=headers_upload,
    )

    # Scenario 4: Upload Fails Mid-Composition

    # User actions:
    # - User selects 3 files
    # - Files 1 and 2 upload successfully, file 3 fails (network error/quota)
    # - User sees error, removes failed file from UI
    # - User submits comment with 2 successful files

    # File 3: Failure
    upload_file(
        client=client,
        request_id=request_id,
        key_base=file3_key_base,
        key_ext=file3_key_ext,
        data_content=file3_data_content,
        headers_upload=headers_upload,
        expected_status_code=400,
        expected_json={"message": "Maximum file size exceeded.", "status": 400},
    )
    # Response: 413 Payload Too Large
    # {
    # "message": "File size exceeds limit",
    # "max_size": 10485760,
    # "actual_size": 15000000
    # }

    # Step 3: Submit comment with file references (only successful uploads)
    comment_id = submit_comment(
        client=client,
        request_id=request_id,
        # file3 not included
        files_details=[file1_details, file2_details],
        events_resource_data_with_empty_files=events_resource_data_with_empty_files,
        headers=headers,
    )

    # Frontend handling:
    # - Track upload state (pending/success/failed)
    # - Only include successful uploads in files array
    # - Show clear error for failed uploads
    # - Allow retry or removal

    # Extra: Verify that both files are present
    access_file_content(
        client=client,
        request_id=request_id,
        key=file1_details["key"],
        data_content=file1_data_content,
        headers=headers,
    )

    access_file_content(
        client=client,
        request_id=request_id,
        key=file2_details["key"],
        data_content=file2_data_content,
        headers=headers,
    )

    # Scenario 3: Delete Attachment from Comment

    # User actions:
    # 1. User clicks “Edit” on comment with 2 attachments
    # 2. User clicks “Remove” on one attachment in the UI
    # 3. User clicks “Update comment”

    # Step 1: Get current comment
    # TODO: In the frontend, we actually use the timeline instead of retrieving one specific comment.
    # GET /api/requests/123/comments/456
    # Response:
    # {
    # "payload": {
    #     "files": [
    #     {"file_id": "abc-...", "key": "uuid-file1.pdf", "original_filename": "file1.pdf", ...},
    #     {"file_id": "def-...", "key": "uuid-file2.pdf", "original_filename": "file2.pdf", ...}
    #     ]
    # }
    # }

    # Step 2: Update comment with reduced files array
    update_comment(
        client=client,
        request_id=request_id,
        comment_id=comment_id,
        # Only second file remains
        files_details=[file2_details],
        events_resource_data_with_empty_files=events_resource_data_with_empty_files,
        headers=headers,
    )

    # Extra: Verify that the first file is not present anymore
    # TODO: The API should not raise exceptions but instead return a failure status code.
    with pytest.raises(FileNotFoundError):
        access_file_content(
            client=client,
            request_id=request_id,
            key=file1_details["key"],
            data_content=file1_data_content,
            headers=headers,
        )

    # Extra: Verify that the second file is still present
    access_file_content(
        client=client,
        request_id=request_id,
        key=file2_details["key"],
        data_content=file2_data_content,
        headers=headers,
    )

    # Backend behavior (ATOMIC):
    # - FileCleanupComponent compares old vs new files arrays
    # - Detects file removed from array (file_id “abc-…” no longer present)
    # - Deletes file automatically in same transaction as comment update
    # - All-or-nothing: If update fails, file NOT deleted
    # - Idempotent: Retry-safe

    # Frontend logic:
    # - Simply sends updated comment with new files array
    # - No separate DELETE request needed!
    # - Backend handles file deletion automatically

    # Note: File remains in storage until DELETE is called.
    # If another comment references the same file (via separate upload),
    # it has a different file_id/key, so deletion doesn’t affect it.


def test_scenario_2(
    app,
    client_logged_as,
    example_request,
    headers,
    headers_upload,
    location,
    events_resource_data_with_empty_files,
):
    # Scenario 2: Update Comment to Add Attachments

    # User actions:
    # 1. User clicks “Edit” on existing comment (no attachments currently)
    # 2. User modifies text to add “EDIT: forgot to attach PDF files”
    # 3. User selects 2 PDF files to attach
    # 4. User clicks “Update comment”

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

    # Step 0: Submit a comment without files
    comment_id = submit_comment(
        client=client,
        request_id=request_id,
        files_details=[],
        events_resource_data_with_empty_files=events_resource_data_with_empty_files,
        headers=headers,
    )

    # Step 1: Get current comment
    # TODO: In the frontend, we actually use the timeline instead of retrieving one specific comment.
    # GET /api/requests/123/comments/456
    # Response:
    # {
    # "id": "comment-456",
    # "payload": {
    #     "content": "Original text",
    #     "format": "html",
    #     "files": []  // No attachments yet
    # }
    # }

    # Step 2: Upload new files (same as Scenario 1)
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

    # Step 3: Update comment with new content and files
    update_comment(
        client=client,
        request_id=request_id,
        comment_id=comment_id,
        files_details=[file1_details, file2_details],
        events_resource_data_with_empty_files=events_resource_data_with_empty_files,
        headers=headers,
    )

    # Extra: Verify that both files are present
    access_file_content(
        client=client,
        request_id=request_id,
        key=file1_details["key"],
        data_content=file1_data_content,
        headers=headers,
    )

    access_file_content(
        client=client,
        request_id=request_id,
        key=file2_details["key"],
        data_content=file2_data_content,
        headers=headers,
    )


def test_scenario_5(
    app,
    client_logged_as,
    example_request,
    headers,
    headers_upload,
    location,
    events_resource_data_with_empty_files,
):
    # Scenario 5: File Deleted Between Upload and Submit

    # User actions:
    # - User uploads file, gets file_id
    # - Admin/other user deletes file before comment is submitted
    # - User tries to submit comment

    # Passing the `location` fixture to make sure that a default bucket location is defined.
    assert location.default == True

    request_id = example_request.id

    file1_key_base = "screenshot"
    file1_key_ext = ".png"
    file1_data_content = b"\x89PNG\r\n\x1a\n ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    # Step 1: Upload
    client = client_logged_as("user1@example.org")
    file1_details = upload_file(
        client=client,
        request_id=request_id,
        key_base=file1_key_base,
        key_ext=file1_key_ext,
        data_content=file1_data_content,
        headers_upload=headers_upload,
    )

    # Step 2: (Admin deletes file)
    client = client_logged_as("admin@example.org")
    delete_file(
        client=client,
        request_id=request_id,
        key=file1_details["key"],
        headers=headers,
    )

    # Extra: Deleting the file again should fail
    # TODO: The API should not raise exceptions but instead return a failure status code.
    with pytest.raises(FileNotFoundError):
        delete_file(
            client=client,
            request_id=request_id,
            key=file1_details["key"],
            headers=headers,
        )

    # Step 3: User submits
    client = client_logged_as("user1@example.org")
    # TODO: The API should not raise exceptions but instead return a failure status code.
    with pytest.raises(ValueError):
        submit_comment(
            client=client,
            request_id=request_id,
            files_details=[file1_details],
            events_resource_data_with_empty_files=events_resource_data_with_empty_files,
            headers=headers,
        )
    # Response: 400 Bad Request
    # {
    #   "errors": [{
    #     "field": "payload.files[0]",
    #     "messages": ["File abc-... not found"]
    #   }]
    # }

    # Frontend handling:
    # - Show error highlighting problematic attachment
    # - Allow user to re-upload or remove from comment
    # - Validation component should include file_id in error for identification


def test_scenario_deleted_comment_with_files(
    app,
    client_logged_as,
    example_request,
    headers,
    headers_upload,
    location,
    events_resource_data_with_empty_files,
):
    # Scenario: Deleted Comment with Attachments

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

    # Step 1: Upload first file
    file1_details = upload_file(
        client=client,
        request_id=request_id,
        key_base=file1_key_base,
        key_ext=file1_key_ext,
        data_content=file1_data_content,
        headers_upload=headers_upload,
    )

    # Step 2: Upload second file
    file2_details = upload_file(
        client=client,
        request_id=request_id,
        key_base=file2_key_base,
        key_ext=file2_key_ext,
        data_content=file2_data_content,
        headers_upload=headers_upload,
    )

    # Step 3: Submit comment with file references
    comment_id = submit_comment(
        client=client,
        request_id=request_id,
        files_details=[file1_details, file2_details],
        events_resource_data_with_empty_files=events_resource_data_with_empty_files,
        headers=headers,
    )

    # Step 4: Delete the comment
    delete_comment(
        client=client,
        request_id=request_id,
        comment_id=comment_id,
        headers=headers,
    )

    # Extra: Verify that the files are not present anymore
    # TODO: The API should not raise exceptions but instead return a failure status code.
    with pytest.raises(FileNotFoundError):
        access_file_content(
            client=client,
            request_id=request_id,
            key=file1_details["key"],
            data_content=file1_data_content,
            headers=headers,
        )

    # TODO: The API should not raise exceptions but instead return a failure status code.
    with pytest.raises(FileNotFoundError):
        access_file_content(
            client=client,
            request_id=request_id,
            key=file2_details["key"],
            data_content=file2_data_content,
            headers=headers,
        )


def test_scenario_comment_with_invalid_files(
    app,
    client_logged_as,
    example_request,
    headers,
    headers_upload,
    location,
    events_resource_data_with_empty_files,
):
    # Scenario: Comment with invalid Attachments

    # Passing the `location` fixture to make sure that a default bucket location is defined.
    assert location.default == True

    request_id = example_request.id

    file1_details = {
        "file_id": "4e69f1fd-4691-414a-976e-1cf834f8010d",
    }
    file2_details = {
        "file_id": "e9e7193e-f70b-4f52-a0cb-b977b9d1a059",
    }

    # file1_key_base = "screenshot"
    # file1_key_ext = ".png"
    # file1_data_content = b"\x89PNG\r\n\x1a\n ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    # file2_key_base = "report"
    # file2_key_ext = ".pdf"
    # file2_data_content = b"%PDF ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    client = client_logged_as("user1@example.org")

    # Step 3: Submit comment with invalid file references
    # TODO: The API should not raise exceptions but instead return a failure status code.
    with pytest.raises(ValueError):
        submit_comment(
            client=client,
            request_id=request_id,
            files_details=[file1_details, file2_details],
            events_resource_data_with_empty_files=events_resource_data_with_empty_files,
            headers=headers,
        )

    raise ValueError("Get timeline and make sure that the comment is not persisted")


def access_file(client, request_id, key, data_content, headers):
    # Access the file.
    response = client.get(
        f"/requests/{request_id}/files/{key}",
        headers=headers,
    )
    assert 200 == response.status_code
    assert data_content == response.data


# This works too, but maybe it should not since the UI should not be initialized here?
def test_scenario_image_ui_url_bis(app, client_logged_as, headers, example_request):

    client = client_logged_as("user1@example.org")

    request_id = example_request.id
    response = client.get(
        f"/requests/{request_id}/files/abc.txt",
    )
    assert 200 == response.status_code

    # request_id = 1
    key = "abc.txt"
    data_content = "abc"
    access_file(client, request_id, key, data_content, headers)
