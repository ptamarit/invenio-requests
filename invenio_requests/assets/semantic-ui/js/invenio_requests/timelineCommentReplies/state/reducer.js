// This file is part of InvenioRequests
// Copyright (C) 2025 CERN.
//
// Invenio Requests is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import {
  CLEAR_DRAFT,
  HAS_ERROR,
  HAS_DATA,
  IS_LOADING,
  IS_SUBMISSION_COMPLETE,
  IS_SUBMITTING,
  REPLY_APPEND_DRAFT_CONTENT,
  REPLY_DELETE_COMMENT,
  REPLY_RESTORE_DRAFT_CONTENT,
  REPLY_SET_DRAFT_CONTENT,
  REPLY_UPDATE_COMMENT,
  SET_PAGE,
  IS_REPLYING,
  IS_NOT_REPLYING,
} from "./actions";
import _cloneDeep from "lodash/cloneDeep";
import { i18next } from "@translations/invenio_requests/i18next";

// Store lists of child comments and status objects, both grouped by parent request event ID.
// This follows Redux recommendations for a neater and more maintainable state shape: https://redux.js.org/usage/structuring-reducers/normalizing-state-shape#designing-a-normalized-state
export const initialState = {
  childComments: {},
  status: {},
};

export const selectCommentChildren = (state, parentRequestEventId) => {
  const { childComments } = state;
  if (Object.prototype.hasOwnProperty.call(childComments, parentRequestEventId)) {
    return childComments[parentRequestEventId];
  } else {
    return [];
  }
};

const initialRepliesStatus = {
  totalReplyCount: 0,
  loading: false,
  submitting: false,
  error: null,
  page: 1,
  pageSize: 5,
  hasMore: false,
  draftContent: "",
  storedDraftContent: "",
  appendedDraftContent: "",
  isReplying: false,
};

export const selectCommentRepliesStatus = (state, parentRequestEventId) => {
  const { status } = state;
  if (Object.prototype.hasOwnProperty.call(status, parentRequestEventId)) {
    return { ...initialRepliesStatus, ...status[parentRequestEventId] };
  } else {
    return initialRepliesStatus;
  }
};

const newChildCommentsWithUpdate = (childComments, updatedComment) => {
  const newChildComments = _cloneDeep(childComments);
  const index = newChildComments.findIndex((c) => c.id === updatedComment.id);
  newChildComments[index] = updatedComment;
  return newChildComments;
};

const newChildCommentsWithDelete = (childComments, deletedCommentId) => {
  const deletedComment = childComments.find((c) => c.id === deletedCommentId);
  return newChildCommentsWithUpdate(childComments, {
    ...deletedComment,
    type: "L",
    payload: {
      content: "comment was deleted",
      format: "html",
      event: "comment_deleted",
    },
  });
};

// Partially update the status for a given parent event, leaving everything else unchanged.
const newStateWithUpdatedStatus = (state, parentRequestEventId, newStatus) => {
  return {
    ...state,
    status: {
      ...state.status,
      [parentRequestEventId]: {
        ...selectCommentRepliesStatus(state, parentRequestEventId),
        ...newStatus,
      },
    },
  };
};

export const timelineRepliesReducer = (state = initialState, action) => {
  switch (action.type) {
    case IS_LOADING:
      return newStateWithUpdatedStatus(state, action.payload.parentRequestEventId, {
        loading: true,
        error: null,
      });
    case IS_SUBMITTING:
      return newStateWithUpdatedStatus(state, action.payload.parentRequestEventId, {
        submitting: true,
      });
    case IS_SUBMISSION_COMPLETE:
      return newStateWithUpdatedStatus(state, action.payload.parentRequestEventId, {
        submitting: false,
        draftContent: "",
      });
    case IS_REPLYING:
      return newStateWithUpdatedStatus(state, action.payload.parentRequestEventId, {
        isReplying: true,
      });
    case IS_NOT_REPLYING:
      return newStateWithUpdatedStatus(state, action.payload.parentRequestEventId, {
        isReplying: false,
      });
    case HAS_DATA:
      return {
        ...newStateWithUpdatedStatus(state, action.payload.parentRequestEventId, {
          loading: false,
          error: null,
          hasMore: action.payload.hasMore,
          page: action.payload.nextPage,
          // Don't set if not specified
          ...(action.payload.pageSize ? { pageSize: action.payload.pageSize } : {}),
          // Either set if `totalCount` is defined, or increment if `newCount` is defined
          ...(action.payload.totalCount
            ? { totalReplyCount: action.payload.totalCount }
            : action.payload.newCount
            ? {
                totalReplyCount:
                  selectCommentRepliesStatus(state, action.payload.parentRequestEventId)
                    .totalReplyCount + action.payload.newCount,
              }
            : {}),
        }),
        childComments: {
          ...state.childComments,
          // Either prepend or append depending on the requested position
          [action.payload.parentRequestEventId]:
            action.payload.position === "top"
              ? [
                  // Prepend the new comments so they're shown at the top of the list.
                  ...action.payload.newChildComments,
                  ...selectCommentChildren(state, action.payload.parentRequestEventId),
                ]
              : [
                  ...selectCommentChildren(state, action.payload.parentRequestEventId),
                  // Append the new comments since they are newer
                  ...action.payload.newChildComments,
                ],
        },
      };
    case HAS_ERROR:
      return newStateWithUpdatedStatus(state, action.payload.parentRequestEventId, {
        error: action.payload.error,
        loading: false,
        submitting: false,
      });
    case SET_PAGE:
      return newStateWithUpdatedStatus(state, action.payload.parentRequestEventId, {
        page: action.payload.page,
      });
    case REPLY_SET_DRAFT_CONTENT:
      return newStateWithUpdatedStatus(state, action.payload.parentRequestEventId, {
        draftContent: action.payload.content,
      });

    case REPLY_RESTORE_DRAFT_CONTENT:
      return newStateWithUpdatedStatus(state, action.payload.parentRequestEventId, {
        draftContent: action.payload.content,
        storedDraftContent: action.payload.content,
      });

    case REPLY_APPEND_DRAFT_CONTENT:
      return newStateWithUpdatedStatus(state, action.payload.parentRequestEventId, {
        draftContent:
          selectCommentRepliesStatus(state, action.payload.parentRequestEventId)
            .draftContent + action.payload.content,
        appendedDraftContent:
          selectCommentRepliesStatus(state, action.payload.parentRequestEventId)
            .draftContent + action.payload.content,
        isReplying: true,
      });
    case CLEAR_DRAFT:
      return newStateWithUpdatedStatus(state, action.payload.parentRequestEventId, {
        draftContent: "",
        storedDraftContent: "",
      });
    case REPLY_UPDATE_COMMENT:
      return {
        ...newStateWithUpdatedStatus(state, action.payload.parentRequestEventId, {
          submitting: false,
        }),
        childComments: {
          ...state.childComments,
          [action.payload.parentRequestEventId]: newChildCommentsWithUpdate(
            selectCommentChildren(state, action.payload.parentRequestEventId),
            action.payload.updatedComment
          ),
        },
      };
    case REPLY_DELETE_COMMENT:
      return {
        ...newStateWithUpdatedStatus(state, action.payload.parentRequestEventId, {
          submitting: false,
        }),
        childComments: {
          ...state.childComments,
          [action.payload.parentRequestEventId]: newChildCommentsWithDelete(
            selectCommentChildren(state, action.payload.parentRequestEventId),
            action.payload.deletedCommentId
          ),
        },
      };
    default:
      return state;
  }
};
