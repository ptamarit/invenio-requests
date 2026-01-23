# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.


"""Request views module."""

from flask import g

from invenio_requests.proxies import current_files_service


def get_file_content(pid_value, file_key):
    """Get the file content."""
    file = current_files_service.get_file_content(
        identity=g.identity,
        id_=pid_value,
        file_key=file_key,
    )

    return file.send_file(as_attachment=True)
