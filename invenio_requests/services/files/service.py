# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Requests service."""

from os.path import splitext
from uuid import UUID

from base32_lib import base32
from invenio_db import db
from invenio_records_resources.services import FileService, ServiceSchemaWrapper
from invenio_records_resources.services.uow import unit_of_work


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

    # def _create_object_version(bucket, file_stream, filename, mimetype):
    #     object_version = ObjectVersion.create(
    #         bucket=bucket, key=filename, mimetype=mimetype
    #     )
    #     current_app.logger.info(f"Creating object version: {object_version}")
    #     object_version.set_contents(file_stream)
    #     db.session.add(object_version)
    #     db.session.commit()

    # TODO: Other methods have the params file_key, not key.
    @unit_of_work()
    def create_file(self, identity, id_, key, stream, content_length, uow=None):
        """Upload a file in a single operation (simple endpoint).

        Convenience method that combines init/upload/commit into one operation.
        """
        # Permission check, lazy bucket init, file size validation,
        # unique key generation, upload and commit

        # resolve and check permissions
        request = self.request_cls.get_record(id_)
        # self.check_revision_id(request, revision_id)
        self.require_permission(identity, "create_comment", request=request)
        self.require_permission(identity, "update", record=request, request=request)
        # self.require_permission(
        #         identity, "update_comment", request=request, event=event
        # )

        # TODO: Is this atomic? unit_of_work does it?
        if request.files.bucket is None:
            request.files.create_bucket()
            # default_location=Location.get_default().id,
            # default_storage_class=current_app.config[
            #     "FILES_REST_DEFAULT_STORAGE_CLASS"
            # ],
            # db.session.add(bucket)
            # db.session.commit()

        # TODO: Is some validation needed on the filename to avoid weird characters?
        unique_id = base32.generate(length=10, split_every=5, checksum=True)
        key_root, key_ext = splitext(key)
        unique_key = f"{key_root}-{unique_id}{key_ext}"
        request.files[unique_key] = stream
        # Store the original filename in RequestFileMetadata.json (field from RecordMetadataBase)
        request.files[unique_key].model.data = {"original_filename": key}

        # TODO: If files are uploaded/deleted in parallel, this raises:
        # sqlalchemy.orm.exc.StaleDataError: UPDATE statement on table 'request_metadata' expected to update 1 row(s); 0 were matched.
        request.commit()

        db.session.commit()
        # // TODO: Check files in records.
        # When indexing, dumper dumps more information in OpenSearch.
        # Not expand flag, resolvable entity, easier than expand madness.
        # Pre-dump, post-dump, or specific file dumper.

        # run components
        # self.run_components("delete", identity, record=request, uow=uow)

        # we're not using "self.schema" b/c the schema may differ per
        # request type!
        # schema = self._wrap_schema(request.type.marshmallow_schema())

        # Get and run the request type's create action.
        # self._execute(identity, request, request.type.delete_action, uow)

        # uow.register(RecordDeleteOp(request, indexer=self.indexer))

        file_object_model = request.files[unique_key].file.object_model

        # breakpoint()

        # TODO: Return a proper result_item.
        result = request.files[unique_key].file.dumps()

        result["id"] = result.pop("file_id")
        result["key"] = unique_key
        result["metadata"] = {"original_filename": key}
        result.pop("ext")
        result.pop("object_version_id")
        result["links"] = {
            "self": f"/api/requests/{id_}/files/{unique_key}",
            "content": f"/api/requests/{id_}/files/{unique_key}/content",
            "commit": f"/api/requests/{id_}/files/{unique_key}/commit",
            "download_html": f"/requests/{id_}/files/{unique_key}",
        }

        return result

        # return self.result_item(
        #     self,
        #     identity,
        #     # request.files[unique_key].file,
        #     # request.files[unique_key].file.dumps(),
        #     file_object_model,
        #     # request,
        #     # schema=self._wrap_schema(file_object_model.type.marshmallow_schema()),
        #     # schema=RequestFileSchema,
        #     # TODO: Fix links_tpl
        #     # links_tpl=self.files.file_links_item_tpl(id_),
        #     # links_tpl=self.links_tpl_factory(
        #     #     self.config.links_item, request_type=str(request.type)
        #     # ),
        # )

    def read_file_metadata(self, identity, id_, file_key):
        """Retrieve file metadata."""
        # resolve and check permissions
        request = self.request_cls.get_record(id_)
        self.require_permission(identity, "read", request=request)
        # Return file metadata (key, size, mimetype, links, etc.)

    def get_file(self, identity, id_, file_key):
        """Retrieve file content for download/display."""
        # resolve and check permissions
        request = self.request_cls.get_record(id_)
        # self.require_permission(identity, 'read', record=record)
        self.require_permission(identity, "read", request=request)
        # Return file stream

        request_file = request.files.get(file_key)
        if request_file is None:
            raise FileNotFoundError()
        # return self.result_item(
        #     self,
        #     identity,
        #     request_file,
        #     request,
        #     # links_tpl=self.files.file_links_item_tpl(id_),
        # )
        return request_file.file

    def list_files(self, identity, id_):
        """List all files for a request."""
        # resolve and check permissions
        request = self.request_cls.get_record(id_)
        self.require_permission(identity, "read", request=request)
        # Return list of all files in request bucket
        return list(request.files.keys())

    @unit_of_work()
    def delete_file(self, identity, id_, file_key=None, file_id=None, uow=None):
        """Delete a specific file."""
        # Called explicitly via API or by frontend when file removed from comment

        if file_key is None and file_id is None:
            raise ValueError("Argument file_key or file_id required")

        # resolve and check permissions
        request = self.request_cls.get_record(id_)
        # self.require_permission(identity, "action_delete", request=request)
        self.require_permission(identity, "update", record=request, request=request)
        # self.require_permission(
        #     identity, "delete_comment", request=request, event=event
        # )
        # self.require_permission(
        #     identity, "update_comment", request=request, event=event
        # )

        # TODO: Why not doing request.files.delete(file_key) ?
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
            raise FileNotFoundError()

        # TODO: If files are uploaded/deleted in parallel, this raises:
        # sqlalchemy.orm.exc.StaleDataError: UPDATE statement on table 'request_metadata' expected to update 1 row(s); 0 were matched.
        request.commit()

        db.session.commit()

        # TODO: Return a proper result_item.
        return deleted_file.file.dumps()
        # return self.result_item(
        #     self,
        #     identity,
        #     deleted_file,
        #     request,
        #     # links_tpl=self.files.file_links_item_tpl(id_),
        # )
