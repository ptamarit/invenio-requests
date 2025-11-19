# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Northwestern University.
# Copyright (C) 2025 CESNET i.a.l.e.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Mock module for registry tests."""

from invenio_users_resources.entity_resolvers import UserResolver

from invenio_requests.customizations import EventType, RequestType


class MockRequestType(RequestType):
    """Mock request type."""

    type_id = "mock"


class MockEventType(EventType):
    """Mock event type."""

    type_id = "M"


class MockResolver(UserResolver):
    """Mock entity resolver."""

    type_id = "mock"
