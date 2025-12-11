// This file is part of InvenioRequests
// Copyright (C) 2022 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.
export const payloadSerializer = (content, format, files) => ({
  payload: {
    content,
    format,
    files: files.map(file => ({
      "file_id": file.file_id,
      // "key": file.key,
      // "original_filename": file.original_filename,
      // "size": 123,
      // "mimetype": "image/png",
      // "created": "2024-01-01",
    })),
  },
});

export const errorSerializer = (error) =>
  error?.response?.data?.message || error?.message;
