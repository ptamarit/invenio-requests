# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Request files service."""

from os.path import splitext
from uuid import UUID

from base32_lib import base32
from flask import current_app
from invenio_db import db
from invenio_records_resources.services import FileService, ServiceSchemaWrapper
from invenio_records_resources.services.uow import RecordCommitOp, unit_of_work

from invenio_requests.services.files.errors import (
    RequestFileArgumentMissingError,
    RequestFileNotFoundError,
    RequestFileSizeLimitError,
)


class RequestFilesService(FileService):
    """Service for managing request file attachments."""

    def _wrap_schema(self, schema):
        """Wrap schema."""
        return ServiceSchemaWrapper(self, schema)

    # Utilities
    @property
    def request_cls(self):
        """Get associated request class."""
        return self.config.request_cls

    @unit_of_work()
    def create_file(self, identity, id_, key, stream, content_length, uow=None):
        """Upload a file in a single operation (simple endpoint).

        Convenience method that combines init/upload/commit into one operation.
        """
        # Resolve and check permissions
        request = self.request_cls.get_record(id_)
        self.require_permission(identity, "manage_files", request=request)

        # File size validation
        max_file_size = current_app.config["REQUESTS_FILES_DEFAULT_MAX_FILE_SIZE"]
        if content_length > max_file_size:
            raise RequestFileSizeLimitError()

        # Unique key generation
        unique_id = base32.generate(length=10, split_every=5, checksum=True)
        key_root, key_ext = splitext(key)
        unique_key = f"{key_root}-{unique_id}{key_ext}"

        # Lazy bucket initialization
        if request.files.bucket is None:
            request.files.create_bucket()

        request.files[unique_key] = stream
        # Store the original filename in RequestFileMetadata.json (field from RecordMetadataBase)
        request.files[unique_key].model.data = {"original_filename": key}

        uow.register(RecordCommitOp(request))

        # TODO: If files are uploaded/deleted in parallel, this raises:
        # sqlalchemy.orm.exc.StaleDataError: UPDATE statement on table 'request_metadata' expected to update 1 row(s); 0 were matched.
        request.commit()

        db.session.commit()

        result = request.files[unique_key].file.dumps()

        result["id"] = result.pop("file_id")
        result["key"] = unique_key
        result["metadata"] = {"original_filename": key}
        result.pop("ext")
        result.pop("object_version_id")
        result["links"] = {
            "self": f"/api/requests/{id_}/files/{unique_key}",
            "content": f"/api/requests/{id_}/files/{unique_key}/content",
            "download_html": f"/requests/{id_}/files/{unique_key}",
        }
        return result

    def get_file_content(self, identity, id_, file_key):
        """Retrieve file content for download/display."""
        # Resolve and check permissions
        request = self.request_cls.get_record(id_)
        self.require_permission(identity, "read_files", request=request)

        # Return file stream
        request_file = request.files.get(file_key)
        if request_file is None:
            raise RequestFileNotFoundError()

        return request_file.file

    @unit_of_work()
    def delete_file(self, identity, id_, file_key=None, file_id=None, uow=None):
        """Delete a specific file."""
        # Called explicitly via API or by frontend when file removed from comment

        if file_key is None and file_id is None:
            raise RequestFileArgumentMissingError()

        # Resolve and check permissions
        request = self.request_cls.get_record(id_)
        self.require_permission(identity, "manage_files", request=request)

        if file_key is not None:
            deleted_file = request.files.pop(file_key, None)
        else:
            deleted_file = None
            file_id_uuid = UUID(file_id)
            for request_file_key in request.files:
                request_file = request.files[request_file_key]
                if request_file.file.id == file_id_uuid:
                    deleted_file = request.files.pop(request_file_key, None)
                    break

        if deleted_file is None:
            raise RequestFileNotFoundError()

        deleted_file.delete(force=True)

        uow.register(RecordCommitOp(request))

        # TODO: If files are uploaded/deleted in parallel, this raises:
        # sqlalchemy.orm.exc.StaleDataError: UPDATE statement on table 'request_metadata' expected to update 1 row(s); 0 were matched.
        request.commit()

        db.session.commit()

        return deleted_file.file.dumps()
