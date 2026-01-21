// This file is part of InvenioRequests
// Copyright (C) 2025 CERN.
//
// Invenio Requests is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { RequestEventsLinksExtractor } from "../api/InvenioRequestEventsApi";

const COMMENT_PREFIX = "#commentevent-";
const REPLY_PREFIX = "#replyevent-";

export const isEventSelected = (event) => {
  const eventUrl = new URL(new RequestEventsLinksExtractor(event.links).eventHtmlUrl);
  const currentUrl = new URL(window.location.href);
  return eventUrl.hash === currentUrl.hash;
};

export const getEventIdFromUrl = () => {
  const currentUrl = new URL(window.location.href);
  const hash = currentUrl.hash;
  let eventId = null;

  if (hash.startsWith(COMMENT_PREFIX)) {
    eventId = hash.substring(COMMENT_PREFIX.length);
  } else if (hash.startsWith(REPLY_PREFIX)) {
    eventId = hash.substring(REPLY_PREFIX.length);
  }

  return eventId;
};

export const isReplyEventInUrl = () => {
  const currentUrl = new URL(window.location.href);
  return currentUrl.hash.startsWith(REPLY_PREFIX);
};
