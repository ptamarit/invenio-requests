# SPDX-FileCopyrightText: 2023 CERN.
# SPDX-FileCopyrightText: 2025-2026 Graz University of Technology.
# SPDX-FileCopyrightText: 2025 Northwestern University.
# SPDX-License-Identifier: MIT
"""Test user moderation resource."""

import pytest

from invenio_requests.proxies import current_user_moderation_service


@pytest.fixture()
def mod_request(app, user1, moderator_user):
    service = current_user_moderation_service

    request_item = service.request_moderation(moderator_user.identity, user_id=user1.id)
    assert request_item

    return request_item


def test_moderate(app, search_clear, client_logged_as, headers, mod_request):
    # Log as moderator
    client = client_logged_as("mod@example.org")

    response = client.post(
        f"/requests/{mod_request.id}/actions/accept", headers=headers
    )
    assert response.status_code == 200

    response = client.get(
        "/requests",
        headers=headers,
    )
    assert response.status_code == 200
    hits = response.json["hits"]["hits"]
    assert len(hits) == 1
    assert hits[0]["status"] == "accepted"

    # Decline after accepting: invalid
    response = client.post(
        f"/requests/{mod_request.id}/actions/decline", headers=headers
    )
    assert response.status_code == 400


@pytest.mark.parametrize(
    "invalid_action,expected_code",
    [
        ("accept", 403),
        ("decline", 403),
    ],
)
def test_moderate_invalid_user(
    app,
    search_clear,
    client_logged_as,
    headers,
    mod_request,
    invalid_action,
    expected_code,
):
    """Tests that a regular user can't moderate."""
    # Log as a normal user that can't moderate
    client = client_logged_as("user1@example.org")
    response = client.post(
        f"/requests/{mod_request.id}/actions/{invalid_action}", headers=headers
    )
    assert response.status_code == expected_code


@pytest.mark.parametrize(
    "invalid_action,expected_code",
    [
        ("delete", 403),  # invalid action but only system can delete
        ("cancel", 400),  # invalid state transition
        ("submit", 400),  # invalid state transition
        (
            "create",
            403,
        ),  # the action should be invalid and return 400. However, 'authenticated_user' action need is not being considered by the permission policy. Perhaps there's an issue with the tests
        ("invalid", 400),  # action does not exist
    ],
)
def test_invalid_actions_after_submit(
    app,
    search_clear,
    client_logged_as,
    headers,
    mod_request,
    invalid_action,
    expected_code,
):
    """Test invalid actions on a user moderation request.

    After created, moderation requests are submitted. Therefore, some actions are not allowed (e.g. 'cancel' and 'submit').
    Other actions are not permitted for a regular user (e.g 'delete' and 'create').
    Permissions are checked first, actions after. Therefore, 'create' is an invalid action but the user does not have permissions. Therefore,
    the resource returns a HTTP 403 Forbidden instead of a HTTP 400 Bad Request.
    """
    # Log as moderator
    client = client_logged_as("mod@example.org")

    # Execute good action (accept)
    response = client.post(
        f"/requests/{mod_request.id}/actions/accept", headers=headers
    )
    assert response.status_code == 200

    # Execute invalid actions after accepting
    response = client.post(
        f"/requests/{mod_request.id}/actions/{invalid_action}", headers=headers
    )
    assert response.status_code == expected_code


def test_search_as_moderator(app, search_clear, client_logged_as, headers, mod_request):
    """Test search as a moderator."""
    # Log as moderator
    mod_email = "mod@example.org"
    client = client_logged_as(mod_email)

    response = client.get(
        "/requests",
        headers=headers,
    )
    assert response.status_code == 200
    hits = response.json["hits"]["hits"]
    assert len(hits) == 1
    hit = hits[0]
    assert hit["type"] == "user-moderation"
    assert hit["status"] == "submitted"


def test_search_as_user(app, search_clear, client_logged_as, headers, mod_request):
    """Test search as a regular user."""
    client = client_logged_as("user1@example.org")

    response = client.get(
        "/requests",
        headers=headers,
    )
    assert response.status_code == 200
    hits = response.json["hits"]["hits"]
    assert len(hits) == 0


def test_links(app, search_clear, client_logged_as, headers, mod_request):
    """Test links on search."""
    # Log as moderator
    mod_email = "mod@example.org"
    client = client_logged_as(mod_email)

    response = client.get(
        "/requests",
        headers=headers,
    )
    assert response.status_code == 200
    hits = response.json["hits"]["hits"]
    assert len(hits) == 1
    hit = hits[0]
    assert hit["type"] == "user-moderation"
    assert hit["status"] == "submitted"
    links = hit["links"]
    assert set(["accept", "cancel", "decline"]) <= set(links["actions"])

    # Decline and check links again
    # Remove host/api, client is already logged.
    url = links["actions"]["decline"][len("https://127.0.0.1:5000/api") :]
    response = client.post(url, headers=headers)
    assert response.status_code == 200

    response = client.get(
        "/requests",
        headers=headers,
    )
    assert response.status_code == 200
    hits = response.json["hits"]["hits"]
    assert len(hits) == 1
    hit = hits[0]
    links = hit["links"]
    # Actions are not allowed anymore
    assert set(["accept", "cancel", "decline"]) > set(links["actions"])
