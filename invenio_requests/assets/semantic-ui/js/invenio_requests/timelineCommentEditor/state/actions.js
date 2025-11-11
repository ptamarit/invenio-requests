// This file is part of InvenioRequests
// Copyright (C) 2022-2025 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { errorSerializer, payloadSerializer } from "../../api/serializers";
import {
  CHANGE_PAGE,
  clearTimelineInterval,
  setTimelineInterval,
  SUCCESS as TIMELINE_SUCCESS,
} from "../../timeline/state/actions";
import _cloneDeep from "lodash/cloneDeep";

export const IS_LOADING = "eventEditor/IS_LOADING";
export const HAS_ERROR = "eventEditor/HAS_ERROR";
export const SUCCESS = "eventEditor/SUCCESS";
export const SETTING_CONTENT = "eventEditor/SETTING_CONTENT";
export const RESTORE_CONTENT = "eventEditor/RESTORE_CONTENT";

const draftCommentKey = (requestId) => `draft-comment-${requestId}`;
const setDraftComment = (requestId, content) => {
  localStorage.setItem(draftCommentKey(requestId), content);
};
const getDraftComment = (requestId) => {
  return localStorage.getItem(draftCommentKey(requestId));
};
const deleteDraftComment = (requestId) => {
  localStorage.removeItem(draftCommentKey(requestId));
};

export const setEventContent = (content) => {
  return async (dispatch, getState, config) => {
    dispatch({
      type: SETTING_CONTENT,
      payload: content,
    });
    const { request } = getState();

    try {
      setDraftComment(request.data.id, content);
    } catch (e) {
      // This should not be a fatal error. The comment editor is still usable if
      // draft saving isn't working (e.g. on very old browsers or ultra-restricted
      // environments with 0 storage quota.)
      console.warn("Failed to save comment:", e);
    }
  };
};

export const restoreEventContent = () => {
  return (dispatch, getState, config) => {
    const { request } = getState();
    let savedDraft = null;
    try {
      savedDraft = getDraftComment(request.data.id);
    } catch (e) {
      console.warn("Failed to get saved comment:", e);
    }

    if (savedDraft) {
      dispatch({
        type: RESTORE_CONTENT,
        payload: savedDraft,
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
      /* Because of the delay in ES indexing we need to handle the updated state on the client-side until it is ready to be retrieved from the server.
      That includes the pagination logic e.g. changing pages if the current page size is exceeded by a new comment. */

      const response = await config.requestsApi.submitComment(payload);

      const currentPage = timelineState.page;
      const currentSize = timelineState.size;
      const currentCommentsLength = timelineState.data.hits.hits.length;
      const shouldGoToNextPage = currentCommentsLength + 1 > currentSize;

      if (shouldGoToNextPage) {
        dispatch({ type: CHANGE_PAGE, payload: currentPage + 1 });
      }

      dispatch({ type: SUCCESS });

      try {
        deleteDraftComment(request.data.id);
      } catch (e) {
        console.warn("Failed to delete saved comment:", e);
      }

      await dispatch({
        type: TIMELINE_SUCCESS,
        payload: _updatedState(response.data, timelineState, shouldGoToNextPage),
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

const _updatedState = (newComment, timelineState, shouldGoToNextPage) => {
  // return timeline with new comment and pagination logic
  const timelineData = _cloneDeep(timelineState.data);
  const currentHits = timelineData.hits.hits;

  timelineData.hits.hits = shouldGoToNextPage
    ? [newComment]
    : [...currentHits, newComment];

  timelineData.hits.total++;

  return timelineData;
};
