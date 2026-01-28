# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Tests for the provided event types customization mechanisms."""

# TODO: This is fully copied from invenio-pages.

from flask import Flask, current_app

from invenio_requests import InvenioRequests
from invenio_requests.config import (
    REQUESTS_COMMENTS_ALLOWED_EXTRA_HTML_ATTRS,
    REQUESTS_COMMENTS_ALLOWED_EXTRA_HTML_TAGS,
)
from invenio_requests.customizations.event_types import RequestsCommentsSanitizedHTML


def test_extra_allowed_html_tags():
    """Test instance folder loading."""
    app = Flask("testapp")
    InvenioRequests(app)

    assert (
        app.config["REQUESTS_COMMENTS_ALLOWED_EXTRA_HTML_ATTRS"]
        == REQUESTS_COMMENTS_ALLOWED_EXTRA_HTML_ATTRS
    )
    assert (
        app.config["REQUESTS_COMMENTS_ALLOWED_EXTRA_HTML_TAGS"]
        == REQUESTS_COMMENTS_ALLOWED_EXTRA_HTML_TAGS
    )

    app.config["REQUESTS_COMMENTS_ALLOWED_EXTRA_HTML_ATTRS"] = ["a"]
    app.config["REQUESTS_COMMENTS_ALLOWED_EXTRA_HTML_TAGS"] = ["a"]
    InvenioRequests(app)
    assert app.config["REQUESTS_COMMENTS_ALLOWED_EXTRA_HTML_ATTRS"] == ["a"]
    assert app.config["REQUESTS_COMMENTS_ALLOWED_EXTRA_HTML_TAGS"] == ["a"]


def test_requests_comments_sanitized_html_initialization():
    """
    Test the initialization of the RequestsCommentsSanitizedHTML class.

    This test verifies that the default values for 'tags' and 'attrs'
    attributes of a RequestsCommentsSanitizedHTML instance are set to None.
    It asserts that both these attributes are None upon initialization,
    ensuring that the class starts with no predefined allowed tags or attributes.
    """
    html_sanitizer = RequestsCommentsSanitizedHTML()
    assert html_sanitizer.tags is None
    assert html_sanitizer.attrs is None


def test_requests_comments_sanitized_html(app):
    """
    Tests RequestsCommentsSanitizedHTML with custom tags and attributes in an app context.
    Verifies if custom settings are properly applied and reflected in the output.
    """
    with app.app_context():
        # Set up the extra configuration
        current_app.config["REQUESTS_COMMENTS_ALLOWED_EXTRA_HTML_TAGS"] = ["customtag"]
        current_app.config["REQUESTS_COMMENTS_ALLOWED_EXTRA_HTML_ATTRS"] = {
            "customtag": ["data-custom"]
        }

        sanitizer = RequestsCommentsSanitizedHTML()
        sample_html = '<customtag data-custom="value">Test</customtag>'
        result = sanitizer._deserialize(sample_html, None, None)

        assert '<customtag data-custom="value">Test</customtag>' in result
