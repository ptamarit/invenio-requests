# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test RequestReviewersComponent update method."""

import pytest
from marshmallow import ValidationError

from invenio_requests.services.requests.components import RequestReviewersComponent


def test_update_add_reviewers(identity_simple, requests_service, submit_request, users):
    """Test adding reviewers to a request."""
    request = submit_request(identity_simple)
    user2, user3 = users["user2"], users["user3"]

    data = {
        "reviewers": [
            {"user": str(user2.id)},
            {"user": str(user3.id)},
        ]
    }

    component = RequestReviewersComponent(requests_service)
    # user 2 is the one updating the request as the receiver
    component.update(user2.identity, data=data, record=request)
    assert request["reviewers"] == data["reviewers"]


def test_update_remove_reviewers(
    identity_simple, requests_service, submit_request, users
):
    """Test removing reviewers from a request."""
    request = submit_request(identity_simple)
    user2, user3 = users["user2"], users["user3"]
    request["reviewers"] = [
        {"user": str(user2.id)},
        {"user": str(user3.id)},
    ]

    data = {"reviewers": [{"user": str(user2.id)}]}

    component = RequestReviewersComponent(requests_service)
    # user 2 is the one updating the request as the receiver
    component.update(user2.identity, data=data, record=request)

    assert request["reviewers"] == data["reviewers"]


def test_update_replace_reviewers(
    identity_simple, requests_service, submit_request, users
):
    """Test replacing reviewers in a request."""
    request = submit_request(identity_simple)
    user2, user3, user4 = users["user2"], users["user3"], users["user4"]
    request["reviewers"] = [
        {"user": str(user2.id)},
        {"user": str(user3.id)},
    ]

    data = {
        "reviewers": [
            {"user": str(user3.id)},
            {"user": str(user4.id)},
        ]
    }

    component = RequestReviewersComponent(requests_service)
    # user 2 is the one updating the request as the receiver
    component.update(user2.identity, data=data, record=request)

    assert request["reviewers"] == data["reviewers"]


def test_update_no_reviewers_change(
    identity_simple, requests_service, submit_request, users
):
    """Test updating with same reviewers (no change)."""
    request = submit_request(identity_simple)
    user2, user3 = users["user2"], users["user3"]
    existing_reviewers = [
        {"user": str(user2.id)},
        {"user": str(user3.id)},
    ]
    request["reviewers"] = existing_reviewers

    data = {"reviewers": existing_reviewers}

    component = RequestReviewersComponent(requests_service)
    # user 2 is the one updating the request as the receiver
    component.update(user2.identity, data=data, record=request)

    assert request["reviewers"] == existing_reviewers


def test_update_empty_reviewers(
    identity_simple,
    requests_service,
    submit_request,
    users,
):
    """Test removing all reviewers."""
    request = submit_request(identity_simple)
    user2 = users["user2"]
    request["reviewers"] = [{"user": str(user2.id)}]

    data = {"reviewers": []}

    component = RequestReviewersComponent(requests_service)
    # user 2 is the one updating the request as the receiver
    component.update(user2.identity, data=data, record=request)

    assert request["reviewers"] == []


def test_update_validation_reviewers_disabled(
    app, identity_simple, requests_service, submit_request, users
):
    """Test validation when reviewers are disabled."""
    app.config["REQUESTS_REVIEWERS_ENABLED"] = False
    user2 = users["user2"]

    request = submit_request(identity_simple)
    data = {"reviewers": [{"user": str(user2.id)}]}

    component = RequestReviewersComponent(requests_service)

    with pytest.raises(ValidationError, match="Reviewers are not enabled"):
        # user 2 is the one updating the request as the receiver
        component.update(user2.identity, data=data, record=request)

    app.config["REQUESTS_REVIEWERS_ENABLED"] = True


def test_update_validation_max_reviewers_exceeded(
    app, identity_simple, requests_service, submit_request, users
):
    """Test validation when max reviewers limit is exceeded."""
    original_max = app.config.get("REQUESTS_REVIEWERS_MAX_NUMBER", 10)
    app.config["REQUESTS_REVIEWERS_MAX_NUMBER"] = 2
    user2, user3, user4 = users["user2"], users["user3"], users["user4"]

    request = submit_request(identity_simple)
    data = {
        "reviewers": [
            {"user": str(user2.id)},
            {"user": str(user3.id)},
            {"user": str(user4.id)},
        ]
    }

    component = RequestReviewersComponent(requests_service)

    with pytest.raises(ValidationError, match="You can only add up to 2 reviewers"):
        # user 2 is the one updating the request as the receiver
        component.update(user2.identity, data=data, record=request)

    app.config["REQUESTS_REVIEWERS_MAX_NUMBER"] = original_max


def test_update_group_reviewers(
    app, identity_simple, requests_service, submit_request, user2
):
    """Test adding group reviewers."""
    app.config["USERS_RESOURCES_GROUPS_ENABLED"] = True

    request = submit_request(identity_simple)
    data = {
        "reviewers": [
            {"group": "admins"},
            {"group": "editors"},
        ]
    }

    component = RequestReviewersComponent(requests_service)
    # user 2 is the one updating the request as the receiver
    component.update(user2.identity, data=data, record=request)

    assert request["reviewers"] == data["reviewers"]


def test_update_validation_group_reviewers_disabled(
    app, identity_simple, requests_service, submit_request, user2
):
    """Test validation when group reviewers are disabled."""
    app.config["USERS_RESOURCES_GROUPS_ENABLED"] = False

    request = submit_request(identity_simple)
    data = {"reviewers": [{"group": "admins"}]}

    component = RequestReviewersComponent(requests_service)

    with pytest.raises(ValidationError, match="Group reviewers are not enabled"):
        # user 2 is the one updating the request as the receiver
        component.update(user2.identity, data=data, record=request)

    app.config["USERS_RESOURCES_GROUPS_ENABLED"] = True


def test_update_mixed_user_and_group_reviewers(
    app,
    identity_simple,
    requests_service,
    submit_request,
    user2,
):
    """Test adding mixed user and group reviewers."""
    app.config["USERS_RESOURCES_GROUPS_ENABLED"] = True

    request = submit_request(identity_simple)
    data = {
        "reviewers": [
            {"user": str(user2.id)},
            {"group": "admins"},
        ]
    }

    component = RequestReviewersComponent(requests_service)
    # user 2 is the one updating the request as the receiver
    component.update(user2.identity, data=data, record=request)

    assert request["reviewers"] == data["reviewers"]


def test_reviewers_updated_added(requests_service, users):
    """Test _reviewers_updated method when reviewers are added."""
    user2, user3 = users["user2"], users["user3"]
    component = RequestReviewersComponent(requests_service)

    previous_reviewers = [{"user": str(user2.id)}]
    new_reviewers = [
        {"user": str(user2.id)},
        {"user": str(user3.id)},
    ]

    event_type, updated_reviewers = component._reviewers_updated(
        previous_reviewers, new_reviewers
    )

    assert event_type == "added"
    assert updated_reviewers == [{"user": str(user3.id)}]


def test_reviewers_updated_removed(requests_service, users):
    """Test _reviewers_updated method when reviewers are removed."""
    user2, user3 = users["user2"], users["user3"]
    component = RequestReviewersComponent(requests_service)

    previous_reviewers = [
        {"user": str(user2.id)},
        {"user": str(user3.id)},
    ]
    new_reviewers = [{"user": str(user2.id)}]

    event_type, updated_reviewers = component._reviewers_updated(
        previous_reviewers, new_reviewers
    )

    assert event_type == "removed"
    assert updated_reviewers == [{"user": str(user3.id)}]


def test_reviewers_updated_updated(requests_service, users):
    """Test _reviewers_updated method when reviewers are updated (both added and removed)."""
    user2, user3, user4 = users["user2"], users["user3"], users["user4"]
    component = RequestReviewersComponent(requests_service)

    previous_reviewers = [
        {"user": str(user2.id)},
        {"user": str(user3.id)},
    ]
    new_reviewers = [
        {"user": str(user3.id)},
        {"user": str(user4.id)},
    ]

    event_type, updated_reviewers = component._reviewers_updated(
        previous_reviewers, new_reviewers
    )

    assert event_type == "updated"
    assert updated_reviewers == new_reviewers


def test_reviewers_updated_unchanged(requests_service, users):
    """Test _reviewers_updated method when reviewers are unchanged."""
    user2, user3 = users["user2"], users["user3"]
    component = RequestReviewersComponent(requests_service)

    reviewers = [
        {"user": str(user2.id)},
        {"user": str(user3.id)},
    ]

    event_type, updated_reviewers = component._reviewers_updated(reviewers, reviewers)

    assert event_type == "unchanged"
    assert updated_reviewers == reviewers


def test_reviewers_updated_group_reviewers_added(requests_service):
    """Test _reviewers_updated method when group reviewers are added."""
    component = RequestReviewersComponent(requests_service)

    previous_reviewers = [{"group": "admins"}]
    new_reviewers = [
        {"group": "admins"},
        {"group": "editors"},
    ]

    event_type, updated_reviewers = component._reviewers_updated(
        previous_reviewers, new_reviewers
    )

    assert event_type == "added"
    assert updated_reviewers == [{"group": "editors"}]


def test_reviewers_updated_empty_to_reviewers(requests_service, users):
    """Test _reviewers_updated method when going from empty to having reviewers."""
    user2 = users["user2"]
    component = RequestReviewersComponent(requests_service)

    previous_reviewers = []
    new_reviewers = [{"user": str(user2.id)}]

    event_type, updated_reviewers = component._reviewers_updated(
        previous_reviewers, new_reviewers
    )

    assert event_type == "added"
    assert updated_reviewers == new_reviewers


def test_reviewers_updated_all_reviewers_removed(requests_service, users):
    """Test _reviewers_updated method when all reviewers are removed."""
    user3 = users["user3"]
    component = RequestReviewersComponent(requests_service)

    previous_reviewers = [{"user": str(user3.id)}]
    new_reviewers = []

    event_type, updated_reviewers = component._reviewers_updated(
        previous_reviewers, new_reviewers
    )

    assert event_type == "removed"
    assert updated_reviewers == previous_reviewers
