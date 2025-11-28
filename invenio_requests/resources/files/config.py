# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""RequestFile Resource Configuration."""

from invenio_records_resources.resources import RecordResourceConfig
from marshmallow import fields


class RequestFilesResourceConfig(RecordResourceConfig):
    """Request Files resource configuration."""

    blueprint_name = "request_files"
    url_prefix = "/requests"
    routes = {
        # TODO: Why not following the structure PUT `/<id>/files/<key>/content` as in:
        #       https://inveniordm.docs.cern.ch/reference/rest_api_drafts_records/#upload-a-draft-files-content
        "create": "/<id>/files/upload/<key>",  # TODO: Change from id to request_id ? It seems that "request_*" prefix is also a Flask thing.
        "item": "/<id>/files/<key>",
        "list": "/<id>/files",
        # "timeline": "/<request_id>/timeline",
        # "list": "/",
        # "user-prefix": "/user",
        # "item": "/<id>",
        # "action": "/<id>/actions/<action>",
    }

    request_view_args = {
        "id": fields.UUID(),
        "key": fields.Str(),
    }

    # request_search_args = RequestSearchRequestArgsSchema

    # Input
    # WARNING: These "request_*" values have nothing to do with the
    #          "Request" of "RequestEvent". They are related to the Flask
    #          request.
    request_list_view_args = {
        "request_id": fields.UUID(),
    }
    # request_item_view_args = {
    #     "request_id": fields.Str(),
    #     "comment_id": fields.Str(),
    # }

    response_handlers = {
        "application/vnd.inveniordm.v1+json": RecordResourceConfig.response_handlers[
            "application/json"
        ],
        **RecordResourceConfig.response_handlers,
    }
