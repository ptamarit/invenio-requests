# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2021 CERN.
# Copyright (C) 2024 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test alembic recipes for Invenio-RDM-Records."""

import pytest
from invenio_db.utils import alembic_test_context, drop_alembic_version_table


def test_alembic(base_app, database):
    """Test alembic recipes."""
    db = database
    ext = base_app.extensions["invenio-db"]

    if db.engine.name == "sqlite":
        raise pytest.skip("Upgrades are not supported on SQLite.")

    base_app.config["ALEMBIC_CONTEXT"] = alembic_test_context()

    # Check that this package's SQLAlchemy models have been properly registered
    tables = [x for x in db.metadata.tables]
    assert "request_metadata" in tables
    assert "request_events" in tables
    assert "request_files" in tables

    # Check that Alembic agrees that there's no further tables to create.
    assert len(ext.alembic.compare_metadata()) == 0

    # Drop everything and recreate tables all with Alembic
    db.drop_all()
    drop_alembic_version_table()
    ext.alembic.upgrade()
    # FIXME: Failing since SQLAlchemy-Continuum 1.6.0 (works with 1.5.2)
    # assert len(ext.alembic.compare_metadata()) == 0

    # Try to upgrade and downgrade
    ext.alembic.stamp()
    ext.alembic.downgrade(target="96e796392533")
    ext.alembic.upgrade()
    # FIXME: Failing since SQLAlchemy-Continuum 1.6.0 (works with 1.5.2)
    # assert len(ext.alembic.compare_metadata()) == 0

    drop_alembic_version_table()
