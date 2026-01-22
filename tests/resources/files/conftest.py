# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Request Files Resource conftest."""

import pytest


@pytest.fixture()
def headers_upload():
    """Default headers for uploads."""
    return {
        "content-type": "application/octet-stream",
        "accept": "application/json",
    }
