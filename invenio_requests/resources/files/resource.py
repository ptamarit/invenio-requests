# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Requests resource."""


from copy import deepcopy

from flask import g
from flask_resources import resource_requestctx, response_handler, route
from invenio_records_resources.resources import RecordResource
from invenio_records_resources.resources.files.resource import request_stream
from invenio_records_resources.resources.records.resource import (
    request_extra_args,
    request_headers,
    request_view_args,
)
from invenio_records_resources.resources.records.utils import search_preference

from invenio_requests.customizations.event_types import CommentEventType


#
# Resource
#
class RequestFilesResource(RecordResource):
    """Resource for Request files."""

    # TODO: Is this needed?
    def create_blueprint(self, **options):
        """Create the blueprint."""
        # We avoid passing url_prefix to the blueprint because we need to
        # install URLs under both /records and /user/records. Instead we
        # add the prefix manually to each route (which is anyway what Flask
        # does in the end)
        options["url_prefix"] = ""
        return super().create_blueprint(**options)

    def create_url_rules(self):
        """Create the URL rules for the record resource."""
        # Assignment of routes should be part of the
        # Config class
        # routes = self.config.routes
        routes = self.config.routes
        # raise ValueError("/api" + self.config.url_prefix + routes["create"])
        return [
            # route("POST", routes["list"], self.create),
            # Are we sure that we want PUT and not POST?
            route(
                "PUT", "/api" + self.config.url_prefix + routes["create"], self.create
            ),
            # route("GET", routes["item"], self.read),
            # route("PUT", routes["item"], self.update),
            # route("DELETE", routes["item"], self.delete),
            # route("GET", routes["timeline"], self.search),
        ]

        # def p(route):
        #     """Prefix a route with the URL prefix."""
        #     return f"{self.config.url_prefix}{route}"

        # def s(route):
        #     """Suffix a route with the URL prefix."""
        #     return f"{route}{self.config.url_prefix}"

        # return [
        #     route("GET", p(routes["list"]), self.search),
        #     route("GET", p(routes["item"]), self.read),
        #     route("PUT", p(routes["item"]), self.update),
        #     route("DELETE", p(routes["item"]), self.delete),
        #     route("POST", p(routes["action"]), self.execute_action),
        #     route("GET", s(routes["user-prefix"]), self.search_user_requests),
        # ]

    @request_extra_args
    @request_headers
    @request_view_args
    @request_stream
    @response_handler()
    def create(self):
        """Create a file."""
        # data = deepcopy(resource_requestctx.data) if resource_requestctx.data else {}

        item = self.service.create_file(
            identity=g.identity,
            id_=resource_requestctx.view_args["id"],
            key=resource_requestctx.view_args["key"],
            # data=resource_requestctx.data,
            stream=resource_requestctx.data["request_stream"],
            content_length=resource_requestctx.data["request_content_length"],
        )
        # TODO: 201 instead of 200?
        # return item.to_dict(), 200
        return item, 200  # TODO: We need the to_dict like everywhere else.
        # self, identity, id_, key, stream, content_length)

    # @request_extra_args
    # # @request_search_args
    # # @request_view_args
    # @response_handler(many=True)
    # def search(self):
    #     """Perform a search over the items."""
    #     hits = self.service.search(
    #         identity=g.identity,
    #         params=resource_requestctx.args,
    #         search_preference=search_preference(),
    #         expand=resource_requestctx.args.get("expand", False),
    #     )
    #     return hits.to_dict(), 200

    # # @request_view_args
    # def read_logo(self):
    #     """Read logo's content."""
    #     item = self.service.read_logo(
    #         resource_requestctx.view_args["pid_value"],
    #         g.identity,
    #     )
    #     return item.send_file(), 200

    # # @request_view_args
    # # @request_stream
    # @response_handler()
    # def update_logo(self):
    #     """Upload logo content."""
    #     item = self.service.update_logo(
    #         resource_requestctx.view_args["pid_value"],
    #         g.identity,
    #         resource_requestctx.data["request_stream"],
    #         content_length=resource_requestctx.data["request_content_length"],
    #     )
    #     return item.to_dict(), 200

    # # @request_view_args
    # def delete_logo(self):
    #     """Delete logo."""
    #     self.service.delete_logo(
    #         resource_requestctx.view_args["pid_value"],
    #         g.identity,
    #     )
    #     return "", 204
