// This file is part of InvenioRequests
// Copyright (C) 2022-2026 CERN.
// Copyright (C) 2024 Northwestern University.
// Copyright (C) 2024 KTH Royal Institute of Technology.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

export const requestDetailsDiv = document.getElementById("request-detail");
export const request = JSON.parse(requestDetailsDiv.dataset.record);
export const defaultQueryParams = JSON.parse(
  requestDetailsDiv.dataset.defaultQueryConfig
);
export const defaultReplyQueryParams = JSON.parse(
  requestDetailsDiv.dataset.defaultReplyQueryConfig
);
export const userAvatar = JSON.parse(requestDetailsDiv.dataset.userAvatar);
export const permissions = JSON.parse(requestDetailsDiv.dataset.permissions);
export const config = JSON.parse(requestDetailsDiv.dataset.config);
