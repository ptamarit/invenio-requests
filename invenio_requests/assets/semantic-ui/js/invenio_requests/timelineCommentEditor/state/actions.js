// This file is part of InvenioRequests
// Copyright (C) 2022-2025 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { errorSerializer, payloadSerializer } from "../../api/serializers";
import {
  clearTimelineInterval,
  setTimelineInterval,
  SUCCESS as TIMELINE_SUCCESS,
} from "../../timeline/state/actions";
import _cloneDeep from "lodash/cloneDeep";

export const IS_LOADING = "eventEditor/IS_LOADING";
export const HAS_ERROR = "eventEditor/HAS_ERROR";
export const SUCCESS = "eventEditor/SUCCESS";
export const PARENT_SET_DRAFT_CONTENT = "eventEditor/SETTING_CONTENT";
export const PARENT_RESTORE_DRAFT_CONTENT = "eventEditor/RESTORE_CONTENT";

const draftCommentKey = (requestId, parentRequestEventId) =>
  `draft-comment-${requestId}${parentRequestEventId ? "-" + parentRequestEventId : ""}`;
export const setDraftComment = (requestId, parentRequestEventId, content) => {
  localStorage.setItem(draftCommentKey(requestId, parentRequestEventId), content);
};
export const getDraftComment = (requestId, parentRequestEventId) => {
  return localStorage.getItem(draftCommentKey(requestId, parentRequestEventId));
};
export const deleteDraftComment = (requestId, parentRequestEventId) => {
  localStorage.removeItem(draftCommentKey(requestId, parentRequestEventId));
};

export const setEventContent = (content, parentRequestEventId, event) => {
  return async (dispatch, getState) => {
    dispatch({
      type: event,
      payload: {
        parentRequestEventId,
        content,
      },
    });
    const { request } = getState();

    try {
      setDraftComment(request.data.id, parentRequestEventId, content);
    } catch (e) {
      // This should not be a fatal error. The comment editor is still usable if
      // draft saving isn't working (e.g. on very old browsers or ultra-restricted
      // environments with 0 storage quota.)
      console.warn("Failed to save comment:", e);
    }
  };
};

export const restoreEventContent = (parentRequestEventId, event) => {
  return (dispatch, getState) => {
    const { request } = getState();
    let savedDraft = null;
    try {
      savedDraft = getDraftComment(request.data.id, parentRequestEventId);
    } catch (e) {
      console.warn("Failed to get saved comment:", e);
    }

    if (savedDraft) {
      dispatch({
        type: event,
        payload: {
          parentRequestEventId,
          content: savedDraft,
        },
      });
    }
  };
};

export const submitComment = (content, format) => {
  return async (dispatch, getState, config) => {
    const { timeline: timelineState, request } = getState();

    dispatch(clearTimelineInterval());

    dispatch({
      type: IS_LOADING,
    });

    const payload = payloadSerializer(content, format || "html");

    try {
      /* Because of the delay in ES indexing we need to handle the updated state on the client-side until it is ready to be retrieved from the server.*/

      const response = await config.requestsApi.submitComment(payload);

      dispatch({ type: SUCCESS });

      try {
        deleteDraftComment(request.data.id);
      } catch (e) {
        console.warn("Failed to delete saved comment:", e);
      }

      await dispatch({
        type: TIMELINE_SUCCESS,
        payload: _updatedState(response.data, timelineState),
      });
      dispatch(setTimelineInterval());
    } catch (error) {
      dispatch({
        type: HAS_ERROR,
        payload: errorSerializer(error),
      });

      dispatch(setTimelineInterval());

      // throw it again, so it can be caught in the local state
      throw error;
    }
  };
};

const _updatedState = (newComment, timelineState) => {
  // return timeline with new comment
  const timelineData = _cloneDeep(timelineState);

  // Multi-page: append to lastPageData
  timelineData.lastPageHits.push(newComment);
  timelineData.totalHits += 1;

  return timelineData;
};
