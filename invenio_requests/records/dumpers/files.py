# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Dumps files details into the indexed request event record."""

from uuid import UUID

from invenio_records.dumpers import SearchDumperExt

# from invenio_records_resources.records.api import FileRecord
from invenio_records_resources.references import EntityGrant


class FilesDumperExt(SearchDumperExt):
    """Search dumper extension for files fields."""

    files_field = "files"

    def __init__(self):
        """Constructor."""
        super().__init__()

    # TODO: Name the arg record instead of request_event?
    def dump(self, request_event, data):
        """Dump files details into indexed request event."""
        # """Dump the data."""

        # TODO: Better to get the request_id and list of files from `data` or `request_event`?
        # [UUID(file["file_id"]) for file in request_event["payload"].get("files", [])]

        # The test test_delete_non_comment does not provide a payload so we use get to be safe here.
        # payload_files = data["payload"].get("files", [])
        payload_files = data.get("payload", {}).get("files", [])

        # Nothing to do if the comment has no files.
        if not payload_files:
            return

        # request_id = data["request_id"]
        request_id = request_event["request_id"]

        # Import here to avoid circular dependency.
        from invenio_requests.records.api import RequestFile

        # TODO: Zach it would be good to
        # Getting all files linked to the request to avoid too many requests.
        # TODO: Filter by list of IDs instead of getting all the files in the request.
        request_files = RequestFile.list_by_record(request_id)
        request_files_by_file_id = {
            request_file.file.file_id: request_file for request_file in request_files
        }

        for payload_file in payload_files:
            payload_file_uuid = UUID(payload_file["file_id"])
            file_details = request_files_by_file_id.get(payload_file_uuid)
            if file_details is None:
                raise ValueError(
                    f"No file with ID {payload_file_uuid} associated with the request {request_id}"
                )

            payload_file["key"] = file_details.file.key
            # TODO: This is not stored in the File metadata, so how can we retrieve it?
            # TODO: Inside a ["metadata"] subkey?
            payload_file["original_filename"] = file_details.model.data[
                "original_filename"
            ]
            payload_file["size"] = file_details.file.size
            payload_file["mimetype"] = file_details.file.mimetype
            payload_file["created"] = file_details.file.created
            # request_files_list.append(request_file.file.file_id)
            # if request_file.file.file_id in request_event_payload_file_ids:
            # results.append(request_file)
            payload_file["links"] = {
                "self": f"/api/requests/{request_id}/files/{file_details.file.key}",
                "content": f"/api/requests/{request_id}/files/{file_details.file.key}/content",
                "download_html": f"/requests/{request_id}/files/{file_details.file.key}",
            }

        # for result in results:
        #     data["payload"]["files"]
        # data[""]
        # breakpoint()

        #     entity = getattr(request_event, field_name)
        #     if isinstance(entity, list):
        #         for e in entity:
        #             for need in request_event.type.entity_needs(e):
        #                 files.append(EntityGrant(field_name, need).token)
        #     else:
        #         for need in request_event.type.entity_needs(entity):
        #             files.append(EntityGrant(field_name, need).token)
        # data[self.grants_field] = files
        # data[self.field] = getattr(record, self.property)

    # TODO: Name the arg record_cls instead of request_event_cls?
    def load(self, data, request_event_cls):
        """Load the data."""
        # data.pop(self.files_field)
        # breakpoint()
        # Called when loading existing comments
        # data["payload"]["files"][0]["file_id"]
        # data["payload"].get("files", [])

        # TODO: Zach, when loading, we should remove the extra info,
        # since we have the system field to have the updated version from the database.

        # TODO: This is useless
        # data.pop(self.files_field, None)
        pass
