// This file is part of InvenioRequests
// Copyright (C) 2025 CERN.
//
// Invenio Requests is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import {
  CLEAR_DRAFT,
  HAS_ERROR,
  HAS_NEW_DATA,
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

// Store lists of child comments and status objects, both grouped by parent request event ID.
// This follows Redux recommendations for a neater and more maintainable state shape: https://redux.js.org/usage/structuring-reducers/normalizing-state-shape#designing-a-normalized-state
export const initialState = {
  commentRepliesData: {},
  commentStatuses: {},
};

export const selectCommentReplies = (state, parentRequestEventId) => {
  const { commentRepliesData } = state;
  if (Object.prototype.hasOwnProperty.call(commentRepliesData, parentRequestEventId)) {
    return commentRepliesData[parentRequestEventId];
  } else {
    return [];
  }
};

// Initial value for a single item in `commentStatuses`
const initialCommentStatus = {
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
  const { commentStatuses } = state;
  // Using `parentRequestEventId in status` is not advised, as the key could be in the prototype: https://stackoverflow.com/a/455366
  // Using status.hasOwnProperty is not allowed by eslint: https://eslint.org/docs/latest/rules/no-prototype-builtins
  if (Object.prototype.hasOwnProperty.call(commentStatuses, parentRequestEventId)) {
    return { ...initialCommentStatus, ...commentStatuses[parentRequestEventId] };
  } else {
    return initialCommentStatus;
  }
};

const newCommentRepliesWithUpdate = (childComments, updatedComment) => {
  const newChildComments = _cloneDeep(childComments);
  const index = newChildComments.findIndex((c) => c.id === updatedComment.id);
  newChildComments[index] = updatedComment;
  return newChildComments;
};

const newCommentRepliesWithDelete = (childComments, deletedCommentId) => {
  const deletedComment = childComments.find((c) => c.id === deletedCommentId);
  return newCommentRepliesWithUpdate(childComments, {
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
    commentStatuses: {
      ...state.commentStatuses,
      [parentRequestEventId]: {
        ...selectCommentRepliesStatus(state, parentRequestEventId),
        ...newStatus,
      },
    },
  };
};

/**
 * Returns an object to include in an item of `commentStatuses`.
 * Either sets `totalReplyCount` if `totalCount` is defined, or increases if `increaseCountBy` is defined
 */
const newOrIncreasedReplyCount = (state, payload) => {
  if (payload.totalCount) {
    return { totalReplyCount: payload.totalCount };
  } else if (payload.increaseCountBy) {
    const status = selectCommentRepliesStatus(state, payload.parentRequestEventId);
    return { totalReplyCount: status.totalReplyCount + payload.increaseCountBy };
  }
  return {};
};

/**
 * Returns the new list of replies, with the new replies either prepended or
 * appended depending on the value of `payload.position`
 */
const prependedOrAppendedCommentReplies = (state, payload) => {
  const existingCommentReplies = selectCommentReplies(
    state,
    payload.parentRequestEventId
  );

  if (payload.position === "top") {
    return [
      // Prepend the new comments so they're shown at the top of the list.
      ...payload.newChildComments,
      ...existingCommentReplies,
    ];
  } else {
    return [
      ...existingCommentReplies,
      // Append the new comments since they are newer
      ...payload.newChildComments,
    ];
  }
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
    case HAS_NEW_DATA:
      return {
        ...newStateWithUpdatedStatus(state, action.payload.parentRequestEventId, {
          loading: false,
          error: null,
          hasMore: action.payload.hasMore,
          page: action.payload.nextPage,
          // Don't set if not specified
          ...(action.payload.pageSize ? { pageSize: action.payload.pageSize } : {}),
          ...newOrIncreasedReplyCount(state, action.payload),
        }),
        commentRepliesData: {
          ...state.commentRepliesData,
          [action.payload.parentRequestEventId]: prependedOrAppendedCommentReplies(
            state,
            action.payload
          ),
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
        commentRepliesData: {
          ...state.commentRepliesData,
          [action.payload.parentRequestEventId]: newCommentRepliesWithUpdate(
            selectCommentReplies(state, action.payload.parentRequestEventId),
            action.payload.updatedComment
          ),
        },
      };
    case REPLY_DELETE_COMMENT:
      return {
        ...newStateWithUpdatedStatus(state, action.payload.parentRequestEventId, {
          submitting: false,
        }),
        commentRepliesData: {
          ...state.commentRepliesData,
          [action.payload.parentRequestEventId]: newCommentRepliesWithDelete(
            selectCommentReplies(state, action.payload.parentRequestEventId),
            action.payload.deletedCommentId
          ),
        },
      };
    default:
      return state;
  }
};
