# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2022 Northwestern University.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Schemas tests."""


def test_load_dump_only_field(app, identity_simple, submit_request, requests_service):
    request = submit_request(identity_simple)
    schema = requests_service._wrap_schema(request.type.marshmallow_schema())

    data, errors = schema.load(
        {"status": "cancelled"},
        context={
            "identity": identity_simple,
            "record": request,
        },
    )

    assert {"is_locked": False} == data
    # This might seem surprising, but it's a side-effect of pre-load cleaning.
    # That the data above doesn't have the "status" field because it is marked as dump_only, is the most important part.
    assert [] == errors


def test_load_additional_field(app, identity_simple, submit_request, requests_service):
    request = submit_request(identity_simple)
    schema = requests_service._wrap_schema(request.type.marshmallow_schema())

    data, errors = schema.load(
        {"receiver": {"user": "42"}},
        context={
            "identity": identity_simple,
            "record": request,
        },
    )

    assert {"receiver": {"user": "42"}, "is_locked": False} == data
    # This might seem surprising, but it's a side-effect of pre-load cleaning.
    # That the data above has the "is_locked" field because it is marked as load_default=False, is the most important part.
    assert [] == errors
