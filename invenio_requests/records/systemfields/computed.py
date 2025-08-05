# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Computed system fields for requests."""

from invenio_db import db
from invenio_records_resources.records.systemfields.calculated import (
    CalculatedField,
)

from ...customizations import CommentEventType


class LastReply(CalculatedField):
    """System field for getting the last reply event."""

    def __init__(self, key=None, use_cache=True):
        """Constructor."""
        super().__init__(key=key, use_cache=use_cache)

    def calculate(self, record):
        """Fetch the last reply event."""
        # TODO: This logic should be pushed up to the `CalculatedField` class. If we the
        # cache has a key for the system field, even if the value is `None`, it means
        # that the value was already calculated or explicitly cached, e.g. in
        # `post_load`.
        obj_cache = getattr(record, "_obj_cache", None)
        if obj_cache is not None and self.attr_name in obj_cache:
            return obj_cache[self.attr_name]

        RequestEvent = record.event_cls
        RequestEventModel = RequestEvent.model_cls

        last_comment = (
            db.session.query(RequestEventModel)
            .filter(
                RequestEventModel.request_id == record.id,
                RequestEventModel.type == CommentEventType.type_id,
            )
            .order_by(RequestEventModel.created.desc())
            .first()
        )

        if last_comment:
            return RequestEvent(data=last_comment.data, model=last_comment)

        return None

    def pre_dump(self, record, data, dumper=None):
        """Called after a record is dumped."""
        last_reply = getattr(record, self.attr_name)
        if last_reply:
            data[self.attr_name] = last_reply.dumps()
        else:
            data[self.attr_name] = None

    def post_load(self, record, data, loader=None):
        """Called after a record was loaded."""
        RequestEvent = record.event_cls

        record.pop(self.attr_name, None)  # Remove the attribute from the record
        last_reply_dump = data.pop(self.attr_name, None)
        last_reply = None
        if last_reply_dump:
            last_reply = RequestEvent.loads(last_reply_dump)
        self._set_cache(record, last_reply)
