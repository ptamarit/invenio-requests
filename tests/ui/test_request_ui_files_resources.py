# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Request UI Files resource tests."""


def access_file(client, request_id, key, data_content, headers):
    # Access the file.
    response = client.get(
        f"/requests/{request_id}/files/{key}",
        headers=headers,
    )
    assert 200 == response.status_code
    assert data_content == response.data


def test_scenario_image_ui_url(
    app, client_logged_as, headers, example_request, example_request_file
):

    client = client_logged_as("user1@example.org")

    access_file(
        client,
        example_request.id,
        example_request_file["key"],
        example_request_file["data"],
        headers,
    )
