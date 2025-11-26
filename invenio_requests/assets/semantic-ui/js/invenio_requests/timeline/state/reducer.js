// This file is part of InvenioRequests
// Copyright (C) 2022 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { i18next } from "@translations/invenio_requests/i18next";
import {
  CHANGE_PAGE,
  HAS_ERROR,
  IS_LOADING,
  IS_REFRESHING,
  MISSING_REQUESTED_EVENT,
  PARENT_DELETED_COMMENT,
  PARENT_UPDATED_COMMENT,
  SUCCESS,
} from "./actions";
import _cloneDeep from "lodash/cloneDeep";

export const initialState = {
  loading: false,
  refreshing: false,
  data: {},
  error: null,
  size: 15,
  page: 1,
  warning: null,
};

const newStateWithUpdate = (updatedRequestEvent, currentTimelineData) => {
  // return timeline with the updated comment
  const timelineState = _cloneDeep(currentTimelineData);
  const currentHits = timelineState.hits.hits;
  const currentCommentKey = currentHits.findIndex(
    (comment) => comment.id === updatedRequestEvent.id
  );

  currentHits[currentCommentKey] = updatedRequestEvent;

  return timelineState;
};

const newStateWithDelete = (requestEventId, currentTimelineData) => {
  // return timeline with the deleted comment replaced by the deletion event
  const timelineState = _cloneDeep(currentTimelineData);
  const currentHits = timelineState.hits.hits;

  const indexCommentToDelete = currentHits.findIndex(
    (comment) => comment.id === requestEventId
  );

  const currentComment = currentHits[indexCommentToDelete];

  const deletionPayload = {
    content: "comment was deleted",
    format: "html",
    event: "comment_deleted",
  };

  currentHits[indexCommentToDelete] = {
    ...currentComment,
    type: "L",
    payload: deletionPayload,
  };

  return timelineState;
};

export const timelineReducer = (state = initialState, action) => {
  switch (action.type) {
    case IS_LOADING:
      return { ...state, loading: true };
    case IS_REFRESHING:
      return { ...state, refreshing: true };
    case SUCCESS:
      return {
        ...state,
        refreshing: false,
        loading: false,
        data: action.payload,
        error: null,
      };
    case HAS_ERROR:
      return {
        ...state,
        refreshing: false,
        loading: false,
        error: action.payload,
      };
    case CHANGE_PAGE:
      return {
        ...state,
        page: action.payload,
        warning: null,
      };
    case MISSING_REQUESTED_EVENT:
      return {
        ...state,
        warning: i18next.t(
          "The requested comment was not found. The first page of comments is shown instead."
        ),
      };
    case PARENT_UPDATED_COMMENT:
      return {
        ...state,
        data: newStateWithUpdate(action.payload.updatedComment, state.data),
      };
    case PARENT_DELETED_COMMENT:
      return {
        ...state,
        data: newStateWithDelete(action.payload.deletedCommentId, state.data),
      };

    default:
      return state;
  }
};
