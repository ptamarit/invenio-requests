// This file is part of InvenioRequests
// Copyright (C) 2022 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { i18next } from "@translations/invenio_requests/i18next";
import {
  HAS_ERROR,
  MISSING_REQUESTED_EVENT,
  PARENT_DELETED_COMMENT,
  PARENT_UPDATED_COMMENT,
  SET_PAGE,
  SET_TOTAL_HITS,
  SET_FOCUSED_PAGE,
  SET_LOADING_MORE,
  APPEND_TO_LAST_PAGE,
  PARENT_SET_DRAFT_CONTENT,
  PARENT_RESTORE_DRAFT_CONTENT,
  HAS_SUBMISSION_ERROR,
  SET_SUBMITTING,
  SET_REFRESHING,
  SET_LOADING,
} from "./actions";
import _cloneDeep from "lodash/cloneDeep";
import { newOrIncreasedTotalHits } from "../../state/utils";
import { defaultQueryParams } from "../../data";

export const initialState = {
  initialLoading: false,
  lastPageRefreshing: false,
  loadingMore: false,
  // Dictionary of form { page_number: []hit }
  hits: {},
  pageNumbers: [],
  totalHits: 0,
  error: null,
  submissionError: null,
  // The page number that the focused event belongs to.
  focusedPage: null,
  warning: null,
  commentContent: "",
  storedCommentContent: null,
  submitting: false,
};

const newStateWithUpdate = (timelineState, updatedComment, page) => {
  const newTimelineState = _cloneDeep(timelineState);
  const index = newTimelineState.hits[page].findIndex(
    (c) => c.id === updatedComment.id
  );
  newTimelineState.hits[page][index] = updatedComment;
  return newTimelineState;
};

const newStateWithDelete = (timelineState, deletedCommentId, page) => {
  const deletedComment = timelineState.hits[page].find(
    (c) => c.id === deletedCommentId
  );
  return newStateWithUpdate(
    timelineState,
    {
      ...deletedComment,
      type: "L",
      payload: {
        content: "comment was deleted",
        format: "html",
        event: "comment_deleted",
      },
    },
    page
  );
};

const appendToLastOrNewPage = (timelineState, hit) => {
  const lastPage = Math.max(...timelineState.pageNumbers);
  const lastPageSize = timelineState.hits[lastPage].length;
  const { size: pageSize } = defaultQueryParams;

  if (lastPageSize >= pageSize) {
    return {
      ...timelineState,
      hits: {
        ...timelineState.hits,
        [lastPage + 1]: [hit],
      },
      pageNumbers: [...timelineState.pageNumbers, lastPage + 1].toSorted(),
    };
  } else {
    return {
      ...timelineState,
      hits: {
        ...timelineState.hits,
        [lastPage]: [...timelineState.hits[lastPage], hit],
      },
    };
  }
};

export const timelineReducer = (state = initialState, action) => {
  switch (action.type) {
    case SET_LOADING:
      return { ...state, initialLoading: action.payload.loading };
    case SET_REFRESHING:
      return { ...state, lastPageRefreshing: action.payload.refreshing };
    case SET_PAGE:
      return {
        ...state,
        hits: {
          ...state.hits,
          [action.payload.page]: action.payload.hits,
        },
        pageNumbers: [...new Set(state.pageNumbers).add(action.payload.page)].toSorted(
          (a, b) => a - b
        ),
      };
    case APPEND_TO_LAST_PAGE:
      return appendToLastOrNewPage(state, action.payload.hit);
    case SET_TOTAL_HITS:
      return {
        ...state,
        ...newOrIncreasedTotalHits(state, action.payload),
      };
    case SET_FOCUSED_PAGE:
      return {
        ...state,
        focusedPage: action.payload.focusedPage,
      };
    case SET_LOADING_MORE:
      return {
        ...state,
        loadingMore: action.payload.loadingMore,
      };
    case SET_SUBMITTING:
      return {
        ...state,
        submitting: action.payload.submitting,
        submissionError: null,
      };
    case HAS_ERROR:
      return {
        ...state,
        lastPageRefreshing: false,
        initialLoading: false,
        error: action.payload,
      };
    case HAS_SUBMISSION_ERROR:
      return {
        ...state,
        submitting: false,
        submissionError: action.payload,
      };
    case MISSING_REQUESTED_EVENT:
      return {
        ...state,
        warning: i18next.t("We couldn't find the comment you were looking for."),
      };
    case PARENT_UPDATED_COMMENT:
      return newStateWithUpdate(
        state,
        action.payload.updatedComment,
        action.payload.page
      );
    case PARENT_DELETED_COMMENT:
      return newStateWithDelete(
        state,
        action.payload.deletedCommentId,
        action.payload.page
      );
    case PARENT_SET_DRAFT_CONTENT:
      return { ...state, commentContent: action.payload.content };
    case PARENT_RESTORE_DRAFT_CONTENT:
      return {
        ...state,
        commentContent: action.payload.content,
        // We'll never change this later, so it can be used as an `initialValue`
        storedCommentContent: action.payload.content,
      };

    default:
      return state;
  }
};
