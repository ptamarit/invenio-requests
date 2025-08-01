# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Component for creating request numbers."""

from flask import current_app
from invenio_i18n import _
from invenio_records_resources.services.records.components import (
    DataComponent,
    ServiceComponent,
)
from marshmallow import ValidationError

from invenio_requests.customizations.event_types import ReviewersUpdatedType
from invenio_requests.proxies import current_events_service


class RequestNumberComponent(ServiceComponent):
    """Component for assigning request numbers to new requests."""

    def create(self, identity, data=None, record=None, **kwargs):
        """Create identifier when record is created."""
        type(record).number.assign(record)


class EntityReferencesComponent(ServiceComponent):
    """Component for initializing a request's entity references."""

    def create(self, identity, data=None, record=None, **kwargs):
        """Initialize the entity reference fields of a request."""
        for field in ("created_by", "receiver", "topic"):
            if field in kwargs:
                setattr(record, field, kwargs[field])


class RequestDataComponent(DataComponent):
    """Request variant of DataComponent using dynamic schema."""

    def update(self, identity, data=None, record=None, **kwargs):
        """Update an existing record (request)."""
        if record.status == "created":
            keys = ("title", "description", "payload", "receiver", "topic")
        else:
            keys = ("title", "description")

        for k in keys:
            if k in data:
                record[k] = data[k]


class RequestReviewersComponent(ServiceComponent):
    """Component for handling request reviewers."""

    def _reviewers_updated(self, previous_reviewers, new_reviewers):
        """Determine the event type based on reviewers added or removed."""
        prev_rev = set()
        updated = []
        for reviewer in previous_reviewers:
            if "user" in reviewer:
                prev_rev.add(f"user:{reviewer['user']}")
            elif "group" in reviewer:
                prev_rev.add(f"group:{reviewer['group']}")
        for reviewer in new_reviewers:
            if "user" in reviewer:
                if f"user:{reviewer['user']}" not in prev_rev:
                    updated.append(reviewer)
            elif "group" in reviewer:
                if f"group:{reviewer['group']}" not in prev_rev:
                    updated.append(reviewer)

        # NOTE this just supports adding OR removing at a time
        # if both are done, we return "updated" for now
        if len(previous_reviewers) > len(new_reviewers):
            return "removed", updated
        elif len(previous_reviewers) < len(new_reviewers):
            return "added", updated
        elif updated:
            return "updated", updated

    def _validate_reviewers(self, reviewers):
        """Validate the reviewers data."""
        reviewers_enabled = current_app.config["REQUESTS_REVIEWERS_ENABLED"]
        reviewers_groups_enabled = current_app.config["USERS_RESOURCES_GROUPS_ENABLED"]
        max_reviewers = current_app.config["REQUESTS_REVIEWERS_MAX_NUMBER"]

        if not reviewers_enabled:
            raise ValidationError(_("Reviewers are not enabled for this request type."))
        if not reviewers_groups_enabled:
            for reviewer in reviewers:
                if "group" in reviewer:
                    raise ValidationError(_("Group reviewers are not enabled."))

        if len(reviewers) > max_reviewers:
            raise ValidationError(
                _(f"You can only add up to {max_reviewers} reviewers.")
            )

    def update(self, identity, data=None, record=None, **kwargs):
        """Update the reviewers of a request."""
        if reviewers := data.get("reviewers", None):
            self._validate_reviewers(reviewers)
            self.service.require_permission(identity, f"action_accept", request=record)

            event_type, updated_reviewers = self._reviewers_updated(
                record.get("reviewers", []), reviewers
            )
            event = ReviewersUpdatedType(
                payload=dict(
                    event="reviewers_updated",
                    content=_(f"{event_type} a reviewer"),
                    reviewers=updated_reviewers,
                )
            )
            _data = dict(payload=event.payload)
            current_events_service.create(
                identity, record.id, _data, event, uow=self.uow
            )
            record["reviewers"] = reviewers


class RequestPayloadComponent(DataComponent):
    """Request variant of DataComponent using dynamic schema."""

    def update(self, identity, data=None, record=None, **kwargs):
        """Update an existing request payload based on permissions."""
        payload = {}
        # take permissions if exist
        permissions = getattr(
            record.type.payload_schema_cls, "field_load_permissions", {}
        )
        if permissions:
            for key in data["payload"]:
                if key in permissions:
                    # permissions should have been checked by now already
                    # so we can assign the new data
                    payload[key] = data["payload"][key]
                else:
                    # keep the old data - no permission to change it
                    # workaround for the lack of patch method
                    payload[key] = record["payload"][key]
            record["payload"] = payload
