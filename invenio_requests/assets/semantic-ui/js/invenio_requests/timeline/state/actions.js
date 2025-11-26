// This file is part of InvenioRequests
// Copyright (C) 2022 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { updateRequest } from "../../request/state/actions";

export const IS_LOADING = "timeline/IS_LOADING";
export const SUCCESS = "timeline/SUCCESS";
export const HAS_ERROR = "timeline/HAS_ERROR";
export const IS_REFRESHING = "timeline/REFRESHING";
export const CHANGE_PAGE = "timeline/CHANGE_PAGE";
export const MISSING_REQUESTED_EVENT = "timeline/MISSING_REQUESTED_EVENT";
export const PARENT_UPDATED_COMMENT = "timeline/PARENT_UPDATED_COMMENT";
export const PARENT_DELETED_COMMENT = "timeline/PARENT_DELETED_COMMENT";

class intervalManager {
  static IntervalId = undefined;

  static setIntervalId(intervalId) {
    this.intervalId = intervalId;
  }

  static resetInterval() {
    clearInterval(this.intervalId);
    delete this.intervalId;
  }
}

export const fetchTimeline = (focusEventId = undefined) => {
  return async (dispatch, getState, config) => {
    const state = getState();
    const { size, page, data: timelineData } = state.timeline;

    dispatch({
      type: IS_REFRESHING,
    });

    try {
      let response;
      if (focusEventId) {
        response = await config.requestsApi.getTimelineFocused(focusEventId, {
          size: size,
        });
      } else {
        response = await config.requestsApi.getTimeline({
          size: size,
          page: page,
          sort: "oldest",
        });
      }

      // Check if timeline has more events than the current state
      const hasMoreEvents = response.data?.hits?.total > timelineData?.hits?.total;
      if (hasMoreEvents) {
        // Check if a LogEvent was added and fetch request
        const actionEventFound = response.data.hits.hits.some(
          (event) =>
            event.type === "L" &&
            config.requestsApi.availableRequestStatuses.includes(event?.payload?.event)
        );

        if (actionEventFound) {
          const response = await config.requestsApi.getRequest();
          dispatch(updateRequest(response.data));
        }
      }

      if (response.data.page !== page) {
        // If a different page was returned (e.g. a specific event ID was requested) we need to update it.
        // This will _not_ trigger a reload of the timeline.
        dispatch({
          type: CHANGE_PAGE,
          payload: response.data.page,
        });
      }

      if (focusEventId && !response.data.hits.hits.some((h) => h.id === focusEventId)) {
        // Show a warning if the event ID in the hash was not found in the response list of events.
        // This happens if the server cannot find the requested event.
        dispatch({
          type: MISSING_REQUESTED_EVENT,
        });
      }

      dispatch({
        type: SUCCESS,
        payload: response.data,
      });
    } catch (error) {
      dispatch({
        type: HAS_ERROR,
        payload: error,
      });
    }
  };
};

export const setPage = (page) => {
  return async (dispatch, getState, config) => {
    dispatch({
      type: CHANGE_PAGE,
      payload: page,
    });
    dispatch({
      type: IS_LOADING,
    });

    await dispatch(fetchTimeline());
  };
};

const timelineReload = (dispatch, getState, config) => {
  const state = getState();
  const { loading, refreshing, error } = state.timeline;
  const { isLoading: isSubmitting } = state.timelineCommentEditor;

  if (error) {
    dispatch(clearTimelineInterval());
  }

  const concurrentRequests = loading && refreshing && isSubmitting;

  if (concurrentRequests) return;

  dispatch(fetchTimeline());
};

export const getTimelineWithRefresh = (focusEventId) => {
  return async (dispatch, getState, config) => {
    dispatch({
      type: IS_LOADING,
    });
    dispatch(fetchTimeline(focusEventId));
    dispatch(setTimelineInterval());
  };
};

export const setTimelineInterval = () => {
  return async (dispatch, getState, config) => {
    const intervalAlreadySet = intervalManager.intervalId;

    if (!intervalAlreadySet) {
      const intervalId = setInterval(
        () => timelineReload(dispatch, getState, config),
        config.refreshIntervalMs
      );
      intervalManager.setIntervalId(intervalId);
    }
  };
};

export const clearTimelineInterval = () => {
  return (dispatch, getState, config) => {
    intervalManager.resetInterval();
  };
};
