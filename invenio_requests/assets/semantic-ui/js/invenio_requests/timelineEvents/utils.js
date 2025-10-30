// This file is part of InvenioRequests
// Copyright (C) 2025 CERN.
//
// Invenio Requests is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { RequestEventsLinksExtractor } from "../api/InvenioRequestEventsApi";

export const isEventSelected = (event) => {
  const eventUrl = new URL(new RequestEventsLinksExtractor(event.links).eventHtmlUrl);
  const currentUrl = new URL(window.location.href);
  return eventUrl.hash === currentUrl.hash;
};

export const getEventIdFromUrl = () => {
  const currentUrl = new URL(window.location.href);
  const hash = currentUrl.hash;
  let eventId = null;
  const commentPrefix = "#commentevent-";
  if (hash.startsWith(commentPrefix)) {
    eventId = hash.substring(commentPrefix.length);
  }
  return eventId;
};
