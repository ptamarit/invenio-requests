# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Request Files ui views module."""

from flask import Blueprint, current_app, render_template
from flask_login import current_user
from invenio_pidstore.errors import PIDDeletedError, PIDDoesNotExistError
from invenio_records_resources.services.errors import PermissionDeniedError

from .requests import read_file


def create_ui_blueprint(app):
    """Register blueprint routes on app."""
    routes = app.config.get("REQUESTS_ROUTES")

    blueprint = Blueprint(
        "invenio_requests_files",
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    # Here we add a non-API endpoint for HTML embedding and downloads,
    # which unlike the API endpoint is not for programmatic file access.
    blueprint.add_url_rule(
        routes["download_file_html"],
        view_func=read_file,
    )

    return blueprint
