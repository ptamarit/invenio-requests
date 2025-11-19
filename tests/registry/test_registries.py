# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CESNET i.a.l.e.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test for entrypoint loading."""

from tests.mock_module import MockEventType, MockRequestType, MockResolver


def test_request_type_registry_entrypoints(app):
    registry = app.extensions["invenio-requests"].request_type_registry
    assert isinstance(registry.lookup("mock"), MockRequestType)


def test_event_type_registry_entrypoints(app):
    registry = app.extensions["invenio-requests"].event_type_registry
    assert isinstance(registry.lookup("M"), MockEventType)


def test_entity_resolvers_registry_entrypoints(app):
    registry = app.extensions["invenio-requests"].entity_resolvers_registry
    assert isinstance(registry.lookup("mock"), MockResolver)
