# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Requests service configuration."""

from invenio_records_resources.services import (
    Link,
    RecordServiceConfig,
    ServiceSchemaWrapper,
)
from invenio_records_resources.services.base.config import ConfiguratorMixin, FromConfig
from invenio_records_resources.services.records.results import RecordItem, RecordList

from invenio_requests.proxies import current_request_type_registry

from ...records.api import Request, RequestFile
from ..permissions import PermissionPolicy
from ..schemas import RequestFileSchema


class RequestFileItem(RecordItem):
    """RequestFile result item."""

    @property
    def id(self):
        """Id property."""
        return self._record.id


class RequestFileList(RecordList):
    """RequestFile result item."""

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


class RequestFileLink(Link):
    """Link variables setter for RequestFile links."""

    @staticmethod
    def vars(obj, vars):
        """Variables for the URI template."""
        request_type = current_request_type_registry.lookup(vars["request_type"])
        vars.update({"request_id": obj.request_id})
        vars.update(request_type._update_link_config(**vars))


class RequestFilesServiceConfig(RecordServiceConfig, ConfiguratorMixin):
    """Requests Files service configuration."""

    service_id = "request_files"

    # common configuration
    permission_action_prefix = ""
    permission_policy_cls = FromConfig(
        "REQUESTS_PERMISSION_POLICY", default=PermissionPolicy
    )
    result_item_cls = RequestFileItem
    result_list_cls = RequestFileList

    # request files-specific configuration
    record_cls = RequestFile  # needed for model queries
    schema = RequestFileSchema  # stored in the API classes, for customization
    request_cls = Request
    indexer_queue_name = "files"

    # links configuration / ResultItem configurations
    links_item = {
        "self": RequestFileLink("{+api}/requests/{request_id}/files/{key}"),
        "content": RequestFileLink("{+api}/requests/{request_id}/files/{key}/content"),
        "download_html": RequestFileLink("{+ui}/requests/{request_id}/files/{key}"),
    }

    components = FromConfig(
        "REQUESTS_FILES_SERVICE_COMPONENTS",
        default=[],
    )
