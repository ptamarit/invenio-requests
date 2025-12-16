// This file is part of InvenioRequests
// Copyright (C) 2022 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { i18next } from "@translations/invenio_requests/i18next";
import {
  HAS_ERROR,
  IS_LOADING,
  IS_REFRESHING,
  MISSING_REQUESTED_EVENT,
  PARENT_DELETED_COMMENT,
  PARENT_UPDATED_COMMENT,
  SUCCESS,
  APPEND_PAGE,
  LOADING_AFTER_FIRST_PAGE,
  LOADING_AFTER_FOCUSED_PAGE,
} from "./actions";
import _cloneDeep from "lodash/cloneDeep";

export const initialState = {
  initialLoading: false,
  lastPageRefreshing: false,
  firstPageHits: [],
  afterFirstPageHits: [],
  focusedPageHits: [],
  afterFocusedPageHits: [],
  lastPageHits: [],
  totalHits: 0,
  error: null,
  size: 15,
  page: 1,
  focusedPage: null,
  lastPage: null,
  warning: null,
  loadingAfterFirstPage: false,
  loadingAfterFocusedPage: false,
};

const newStateWithUpdate = (updatedComment, timelineState) => {
  const timelineClone = _cloneDeep(timelineState);

  const updateHits = (hitsArray) => {
    if (!hitsArray) return;
    const idx = hitsArray.findIndex((c) => c.id === updatedComment.id);
    if (idx !== -1) hitsArray[idx] = updatedComment;
  };

  // Update in firstPageData, afterFirstPageHits, focusedPageData, afterFocusedPageHits, lastPageData
  updateHits(timelineClone.firstPageHits);
  updateHits(timelineClone.afterFirstPageHits);
  updateHits(timelineClone.focusedPageHits);
  updateHits(timelineClone.afterFocusedPageHits);
  updateHits(timelineClone.lastPageHits);

  return timelineClone;
};

const newStateWithDelete = (requestEventId, timelineState) => {
  const timelineClone = _cloneDeep(timelineState);
  const deletionPayload = {
    content: "comment was deleted",
    event: "comment_deleted",
    format: "html",
  };

  const replaceInHits = (hitsArray) => {
    if (!hitsArray) return;
    const idx = hitsArray.findIndex((c) => c.id === requestEventId);
    if (idx !== -1) {
      hitsArray[idx] = {
        ...hitsArray[idx],
        type: "L",
        payload: deletionPayload,
      };
    }
  };

  // Delete in firstPageData, afterFirstPageHits, focusedPageData, afterFocusedPageHits, lastPageData
  replaceInHits(timelineClone.firstPageHits);
  replaceInHits(timelineClone.afterFirstPageHits);
  replaceInHits(timelineClone.focusedPageHits);
  replaceInHits(timelineClone.afterFocusedPageHits);
  replaceInHits(timelineClone.lastPageHits);

  return timelineClone;
};

const newStateWithAppendedHits = (newHits, after, state) => {
  if (after === "first") {
    return {
      ...state,
      afterFirstPageHits: [...state.afterFirstPageHits, ...newHits],
    };
  } else if (after === "focused") {
    return {
      ...state,
      afterFocusedPageHits: [...state.afterFocusedPageHits, ...newHits],
    };
  } else {
    throw new Error("Invalid `after` value");
  }
};

export const timelineReducer = (state = initialState, action) => {
  switch (action.type) {
    case IS_LOADING:
      return { ...state, initialLoading: true };
    case IS_REFRESHING:
      return { ...state, lastPageRefreshing: true };
    case SUCCESS:
      return {
        ...state,
        lastPageRefreshing: false,
        initialLoading: false,
        firstPageHits: action.payload.firstPageHits ?? state.firstPageHits,
        afterFirstPageHits:
          action.payload.afterFirstPageHits ?? state.afterFirstPageHits,
        focusedPageHits: action.payload.focusedPageHits ?? state.focusedPageHits,
        afterFocusedPageHits:
          action.payload.afterFocusedPageHits ?? state.afterFocusedPageHits,
        lastPageHits: action.payload.lastPageHits ?? state.lastPageHits,
        focusedPage: action.payload.focusedPage ?? state.focusedPage,
        lastPage: action.payload.lastPage ?? state.lastPage,
        totalHits: action.payload.totalHits ?? state.totalHits,
        error: null,
      };
    case APPEND_PAGE:
      return {
        ...newStateWithAppendedHits(
          action.payload.newHits,
          action.payload.after,
          state
        ),
        page: action.payload.after === "first" ? action.payload.page : state.page,
        focusedPage:
          action.payload.after === "focusedPage" ? action.payload.page : state.page,
        loadingAfterFirstPage:
          action.payload.after === "first" ? false : state.loadingAfterFirstPage,
        loadingAfterFocusedPage:
          action.payload.after === "focused" ? false : state.loadingAfterFocusedPage,
      };
    case HAS_ERROR:
      return {
        ...state,
        lastPageRefreshing: false,
        initialLoading: false,
        error: action.payload,
      };
    case MISSING_REQUESTED_EVENT:
      return {
        ...state,
        warning: i18next.t("We couldn't find the comment you were looking for."),
      };
    case PARENT_UPDATED_COMMENT:
      return newStateWithUpdate(action.payload.updatedComment, state);
    case PARENT_DELETED_COMMENT:
      return newStateWithDelete(action.payload.deletedCommentId, state);
    case LOADING_AFTER_FIRST_PAGE:
      return {
        ...state,
        loadingAfterFirstPage: true,
      };
    case LOADING_AFTER_FOCUSED_PAGE:
      return {
        ...state,
        loadingAfterFocusedPage: true,
      };

    default:
      return state;
  }
};
