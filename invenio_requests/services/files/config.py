# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Requests service configuration."""

from invenio_records_resources.services import (
    FileServiceConfig,
    Link,
)
from invenio_records_resources.services.base.config import ConfiguratorMixin, FromConfig
from invenio_records_resources.services.files.links import FileEndpointLink
from invenio_records_resources.services.records.results import RecordItem

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


class RequestFileLink(Link):
    """Link variables setter for RequestFile links."""

    @staticmethod
    def vars(obj, vars):
        """Variables for the URI template."""
        vars.update({"request_id": obj.model.record_id, "key": obj.key})
        # Remark: we do not call `request_type._update_link_config`
        # because we do not want file links to be modified depending on the context (e.g. `/me`)


class RequestFilesServiceConfig(FileServiceConfig, ConfiguratorMixin):
    """Requests Files service configuration."""

    service_id = "request_files"

    # common configuration
    permission_action_prefix = ""
    permission_policy_cls = FromConfig(
        "REQUESTS_PERMISSION_POLICY", default=PermissionPolicy
    )
    result_item_cls = RequestFileItem

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

    file_links_item = {
        "self": FileEndpointLink("request_files.read", params=["pid_value", "key"]),
    }

    components = FromConfig(
        "REQUESTS_FILES_SERVICE_COMPONENTS",
        default=[],
    )
