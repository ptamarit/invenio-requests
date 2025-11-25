# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Requests service."""

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
            # raise ValueError("boom")

        # TODO: Is some validation needed on the filename to avoid weird characters?
        request.files[key] = stream
        request.commit()
        db.session.commit()

        # run components
        # self.run_components("delete", identity, record=request, uow=uow)

        # we're not using "self.schema" b/c the schema may differ per
        # request type!
        # schema = self._wrap_schema(request.type.marshmallow_schema())

        # Get and run the request type's create action.
        # self._execute(identity, request, request.type.delete_action, uow)

        # uow.register(RecordDeleteOp(request, indexer=self.indexer))

        file_object_model = request.files[key].file.object_model

        # TODO: Return a proper result_item.
        return request.files[key].file.dumps()

        # return self.result_item(
        #     self,
        #     identity,
        #     # request.files[key].file,
        #     # request.files[key].file.dumps(),
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

    def get_file_content(self, identity, id_, file_key):
        """Retrieve file content for download/display."""
        # resolve and check permissions
        request = self.request_cls.get_record(id_)
        # self.require_permission(identity, 'read', record=record)
        self.require_permission(identity, "read", request=request)
        # Return file stream

        request_file = request.files.get(file_key)
        if request_file is None:
            raise FileNotFoundError()
        return self.files.file_result_item(
            self,
            identity,
            request_file,
            request,
            # links_tpl=self.files.file_links_item_tpl(id_),
        )

    def list_files(self, identity, id_):
        """List all files for a request."""
        # resolve and check permissions
        request = self.request_cls.get_record(id_)
        self.require_permission(identity, "read", request=request)
        # Return list of all files in request bucket
        return list(request.files.keys())

    @unit_of_work()
    def delete_file(self, identity, id_, file_key, uow=None):
        """Delete a specific file."""
        # Called explicitly via API or by frontend when file removed from comment

        # resolve and check permissions
        request = self.request_cls.get_record(id_)
        self.require_permission(identity, "action_delete", request=request)
        self.require_permission(identity, "update", record=request, request=request)
        # self.require_permission(
        #     identity, "delete_comment", request=request, event=event
        # )
        # self.require_permission(
        #     identity, "update_comment", request=request, event=event
        # )

        # TODO: Why not doing request.files.delete(file_key) ?
        deleted_file = request.files.pop(file_key, None)
        if deleted_file is None:
            raise FileNotFoundError()
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
