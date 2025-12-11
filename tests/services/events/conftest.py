# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 TU Wien.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Request Events conftest."""

import pytest

from invenio_requests.customizations.event_types import CommentEventType, LogEventType
from invenio_requests.records.api import RequestEventFormat


@pytest.fixture()
def events_service_data():
    """Input data for the Request Events Service."""
    return dict(
        comment={
            "type": CommentEventType.type_id,
            "payload": {
                "content": "This is a comment.",
                "format": RequestEventFormat.HTML.value,
                "files": [{"file_id": "b503c859-c6d8-4fdd-8885-c84fd0367615"}],
            },
        },
        log={
            "type": LogEventType.type_id,
            "payload": {
                "content": "This is a log event.",
                "format": RequestEventFormat.HTML.value,
                "event": "LOG_EVENT",
            },
        },
    )
