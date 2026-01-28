// This file is part of InvenioRequests
// Copyright (C) 2025 CERN.
//
// Invenio Requests is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { errorSerializer, payloadSerializer } from "../../api/serializers";
import {
  deleteDraftComment,
  setDraftComment,
  deleteDraftFiles,
  // setDraftFiles,
} from "../../timelineCommentEditor/state/actions";
import { selectCommentReplies, selectCommentRepliesStatus } from "./reducer";

export const IS_LOADING = "timelineReplies/IS_LOADING";
export const IS_SUBMITTING = "timelineReplies/IS_SUBMITTING";
export const IS_REPLYING = "timelineReplies/IS_REPLYING";
export const IS_NOT_REPLYING = "timelineReplies/IS_NOT_REPLYING";
export const HAS_NEW_DATA = "timelineReplies/HAS_DATA";
export const IS_SUBMISSION_COMPLETE = "timelineReplies/IS_SUBMISSION_COMPLETE";
export const HAS_ERROR = "timelineReplies/HAS_ERROR";
export const SET_PAGE = "timelineReplies/SET_PAGE";
export const CLEAR_DRAFT = "timelineReplies/CLEAR_DRAFT";
export const REPLY_APPEND_DRAFT_CONTENT = "timelineReplies/APPEND_DRAFT_CONTENT";
export const REPLY_SET_DRAFT_CONTENT = "timelineReplies/SET_DRAFT_CONTENT";
export const REPLY_RESTORE_DRAFT_CONTENT = "timelineReplies/RESTORE_DRAFT_CONTENT";
export const REPLY_SET_DRAFT_FILES = "timelineReplies/SET_DRAFT_FILES";
export const REPLY_RESTORE_DRAFT_FILES = "timelineReplies/RESTORE_DRAFT_FILES";
export const REPLY_UPDATE_COMMENT = "timelineReplies/UPDATE_COMMENT";
export const REPLY_DELETE_COMMENT = "timelineReplies/DELETE_COMMENT";

export const appendEventContent = (parentRequestEventId, content) => {
  return (dispatch, getState) => {
    dispatch({
      type: REPLY_APPEND_DRAFT_CONTENT,
      payload: {
        content,
        parentRequestEventId,
      },
    });

    const { request } = getState();
    try {
      setDraftComment(request.data.id, parentRequestEventId, content);
    } catch (e) {
      console.warn("Failed to save comment:", e);
    }
  };
};

export const setIsReplying = (parentRequestEventId, isReplying) => {
  return (dispatch) => {
    dispatch({
      type: isReplying ? IS_REPLYING : IS_NOT_REPLYING,
      payload: {
        parentRequestEventId,
      },
    });
  };
};

export const setInitialReplies = (parentRequestEvent) => {
  return (dispatch, _, config) => {
    // The server has the children newest-to-oldest, and we need oldest-to-newest so the newest is shown at the bottom.
    const children = (parentRequestEvent.children || []).toReversed();
    const childrenCount = parentRequestEvent.children_count || 0;
    // If we have children_count, check if there are more children than what's in the preview
    // Otherwise, assume no more if children array is empty
    const hasMore = childrenCount > children.length;

    const { defaultReplyQueryParams } = config ?? {};
    const pageSize = defaultReplyQueryParams.size ?? 5;

    dispatch({
      type: HAS_NEW_DATA,
      payload: {
        position: "top",
        parentRequestEventId: parentRequestEvent.id,
        newChildComments: children,
        hasMore: hasMore,
        totalCount: childrenCount,
        nextPage: 2,
        pageSize,
      },
    });
  };
};

export const loadOlderReplies = (parentRequestEvent) => {
  return async (dispatch, getState, config) => {
    const { timelineReplies } = getState();
    const { page } = selectCommentRepliesStatus(timelineReplies, parentRequestEvent.id);
    const commentReplies = selectCommentReplies(timelineReplies, parentRequestEvent.id);
    const { defaultReplyQueryParams } = config ?? {};
    const pageSize = defaultReplyQueryParams.size ?? 5;

    dispatch({
      type: IS_LOADING,
      payload: { parentRequestEventId: parentRequestEvent.id },
    });

    const api = config.requestEventsApi(parentRequestEvent.links);
    const response = await api.getReplies({
      size: pageSize,
      page,
      sort: "newest",
    });

    const hits = response.data.hits.hits;
    const totalLocalCommentCount = commentReplies.length + hits.length;
    const hasMore = totalLocalCommentCount < response.data.hits.total;

    let nextPage = response.data.page;
    if (hasMore) {
      nextPage = response.data.page + 1;
    }

    dispatch({
      type: HAS_NEW_DATA,
      payload: {
        position: "top",
        parentRequestEventId: parentRequestEvent.id,
        hasMore,
        // `hits` is ordered newest-to-oldest, which is correct for the pagination order.
        // But we need to insert the comments oldest-to-newest in the UI.
        newChildComments: hits.toReversed(),
        nextPage: nextPage,
      },
    });
  };
};

export const submitReply = (parentRequestEvent, content, format, files) => {
  return async (dispatch, getState, config) => {
    const { request } = getState();

    dispatch({
      type: IS_SUBMITTING,
      payload: {
        parentRequestEventId: parentRequestEvent.id,
      },
    });

    const payload = payloadSerializer(content, format || "html", files);

    try {
      const response = await config
        .requestEventsApi(parentRequestEvent.links)
        .submitReply(payload);

      try {
        deleteDraftComment(request.data.id, parentRequestEvent.id);
        deleteDraftFiles(request.data.id, parentRequestEvent.id);
      } catch (e) {
        console.warn("Failed to delete saved comment:", e);
      }

      await dispatch({
        type: HAS_NEW_DATA,
        payload: {
          position: "bottom",
          parentRequestEventId: parentRequestEvent.id,
          newChildComments: [response.data],
          increaseCountBy: 1,
        },
      });

      dispatch({
        type: IS_SUBMISSION_COMPLETE,
        payload: {
          parentRequestEventId: parentRequestEvent.id,
        },
      });
    } catch (error) {
      dispatch({
        type: HAS_ERROR,
        payload: {
          parentRequestEventId: parentRequestEvent.id,
          error: errorSerializer(error),
        },
      });

      throw error;
    }
  };
};

export const clearDraft = (parentRequestEvent) => {
  return (dispatch, getState) => {
    const { request } = getState();
    deleteDraftComment(request.data.id, parentRequestEvent.id);
    deleteDraftFiles(request.data.id, parentRequestEvent.id);
    dispatch({
      type: CLEAR_DRAFT,
      payload: {
        parentRequestEventId: parentRequestEvent.id,
      },
    });
  };
};
