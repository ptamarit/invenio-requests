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
            # Are we sure that we want PUT and not POST?
            route("PUT", self.config.url_prefix + routes["create"], self.create),
            # route("GET", routes["item"], self.read),
            # route("PUT", routes["item"], self.update),
            route("DELETE", self.config.url_prefix + routes["item"], self.delete),
            # TODO: How to make this endpoint non-API?
            # route("GET", self.config.url_prefix + routes["item"], self.get_content),  # Non-API endpoint to download with Content-Disposition
            route(
                "GET", self.config.url_prefix + routes["item_content"], self.get_content
            ),  # API endpoint to access file content
            route(
                "GET", self.config.url_prefix + routes["list"], self.list
            ),  # TODO: This is not used in any UI.
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
            # expand=resource_requestctx.args.get("expand", False),
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

    @request_view_args
    def get_content(self):
        """Get the file content."""
        file = self.service.get_file(
            identity=g.identity,
            id_=resource_requestctx.view_args["id"],
            file_key=resource_requestctx.view_args["key"],
        )
        # TODO: Is there a way to send the file with the `original_filename` instead of with the `key`?
        return file.send_file(as_attachment=True)

    #     """Read logo's content."""
    #     item = self.service.read_logo(
    #         resource_requestctx.view_args["pid_value"],
    #         g.identity,
    #     )
    #     return item.send_file(), 200

    # @request_headers
    @request_view_args
    # @response_handler()
    def list(self):
        """List files."""
        files = self.service.list_files(
            identity=g.identity,
            id_=resource_requestctx.view_args["id"],
        )

        # TODO: Return the information about the deleted file?
        return files, 200

    # @request_headers
    @request_view_args
    # @response_handler()
    def delete(self):
        """Delete a file."""
        deleted_file = self.service.delete_file(
            identity=g.identity,
            id_=resource_requestctx.view_args["id"],
            file_key=resource_requestctx.view_args["key"],
        )

        # TODO: Return the information about the deleted file?
        return "", 204
