# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Request Events Service Config."""

from invenio_records_resources.services import (
    Link,
    RecordServiceConfig,
    ServiceSchemaWrapper,
)
from invenio_records_resources.services.base.config import ConfiguratorMixin, FromConfig
from invenio_records_resources.services.records.links import pagination_links
from invenio_records_resources.services.records.results import RecordItem, RecordList

from invenio_requests.proxies import (
    current_request_type_registry,
)

from ...records.api import Request, RequestEvent
from ..permissions import PermissionPolicy
from ..schemas import RequestEventSchema


class RequestEventItem(RecordItem):
    """RequestEvent result item."""

    @property
    def id(self):
        """Id property."""
        return self._record.id


class RequestEventList(RecordList):
    """RequestEvent result item."""

    @property
    def hits(self):
        """Iterator over the hits."""
        for hit in self._results:
            # Load dump
            record = self._service.record_cls.loads(hit.to_dict())

            # Project the record
            schema = ServiceSchemaWrapper(
                self._service, record.type.marshmallow_schema()
            )
            projection = schema.dump(
                record,
                context=dict(
                    identity=self._identity,
                    record=record,
                    meta=hit.meta,
                ),
            )

            if self._links_item_tpl:
                projection["links"] = self._links_item_tpl.expand(
                    self._identity, record
                )

            yield projection


class RequestEventLink(Link):
    """Link variables setter for RequestEvent links."""

    @staticmethod
    def vars(obj, vars):
        """Variables for the URI template."""
        request_type = current_request_type_registry.lookup(vars["request_type"])
        vars.update({"id": obj.id, "request_id": obj.request_id})
        vars.update(request_type._update_link_config(**vars))


class RequestEventsServiceConfig(RecordServiceConfig, ConfiguratorMixin):
    """Config."""

    service_id = "request_events"

    request_cls = Request
    permission_policy_cls = FromConfig(
        "REQUESTS_PERMISSION_POLICY", default=PermissionPolicy
    )
    schema = RequestEventSchema
    record_cls = RequestEvent
    result_item_cls = RequestEventItem
    result_list_cls = RequestEventList
    indexer_queue_name = "events"

    # ResultItem configurations
    links_item = {
        "self": RequestEventLink("{+api}/requests/{request_id}/comments/{id}"),
        "self_html": RequestEventLink("{+ui}/requests/{request_id}#commentevent-{id}"),
    }
    links_search = pagination_links("{+api}/requests/{request_id}/timeline{?args*}")

    components = FromConfig(
        "REQUESTS_EVENTS_SERVICE_COMPONENTS",
        default=[],
    )
