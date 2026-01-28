# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Dumps files details into the indexed request event record."""

from uuid import UUID

from invenio_records.dumpers import SearchDumperExt


class FilesDumperExt(SearchDumperExt):
    """Search dumper extension for files fields."""

    def __init__(self):
        """Constructor."""
        super().__init__()

    def dump(self, request_event, data):
        """Dump files details into indexed request event."""
        payload_files = data.get("payload", {}).get("files", [])

        # Nothing to do if the comment has no files.
        if not payload_files:
            return

        request_id = request_event["request_id"]

        # Import here to avoid circular dependency.
        from invenio_requests.records.api import RequestFile

        # The new list of files received from the current service call.
        payload_file_ids = [
            UUID(payload_file["file_id"]) for payload_file in payload_files
        ]

        # Retrieve the list of files with the given file IDs which are associated to the request.
        request_files = RequestFile.list_by_file_ids(request_id, payload_file_ids)
        request_files_by_file_id = {
            request_file.file.file_id: request_file for request_file in request_files
        }

        # Expand fields with the information retrieved from the persisted files.
        for payload_file in payload_files:
            payload_file_uuid = UUID(payload_file["file_id"])
            file_details = request_files_by_file_id.get(payload_file_uuid)
            # It is possible that the file is not in the database anymore
            # (for instance, this is also called when a comment is deleted),
            # so we simply don't expand if the file is not found.
            if file_details:
                payload_file["key"] = file_details.file.key
                payload_file["original_filename"] = file_details.model.data[
                    "original_filename"
                ]
                payload_file["size"] = file_details.file.size
                payload_file["mimetype"] = file_details.file.mimetype
                payload_file["created"] = file_details.file.created
                payload_file["links"] = {
                    "self": f"/api/requests/{request_id}/files/{file_details.file.key}",
                    "content": f"/api/requests/{request_id}/files/{file_details.file.key}/content",
                    "download_html": f"/requests/{request_id}/files/{file_details.file.key}",
                }

    def load(self, data, request_event_cls):
        """Load the data."""
        payload_files = data.get("payload", {}).get("files", [])

        # Nothing to do if the comment has no files.
        if not payload_files:
            return

        # Remove all the expanded fields and only keep the original file_id keys.
        for payload_file in payload_files:
            payload_file = {"file_id": payload_file["file_id"]}
