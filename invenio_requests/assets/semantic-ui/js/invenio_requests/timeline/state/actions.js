// This file is part of InvenioRequests
// Copyright (C) 2022 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

export const IS_LOADING = "timeline/IS_LOADING";
export const SUCCESS = "timeline/SUCCESS";
export const HAS_ERROR = "timeline/HAS_ERROR";
export const IS_REFRESHING = "timeline/REFRESHING";
export const MISSING_REQUESTED_EVENT = "timeline/MISSING_REQUESTED_EVENT";
export const PARENT_UPDATED_COMMENT = "timeline/PARENT_UPDATED_COMMENT";
export const PARENT_DELETED_COMMENT = "timeline/PARENT_DELETED_COMMENT";
export const APPEND_PAGE = "timeline/APPEND_PAGE";
export const LOADING_AFTER_FIRST_PAGE = "timeline/LOADING_AFTER_FIRST_PAGE";
export const LOADING_AFTER_FOCUSED_PAGE = "timeline/LOADING_AFTER_FOCUSED_PAGE";

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

export const setLoadingForLoadMore = (type) => {
  return {
    type: type,
  };
};

export const appendPage = (payload) => {
  return {
    type: APPEND_PAGE,
    payload: payload,
  };
};

export const fetchTimeline = (focusEventId = undefined) => {
  return async (dispatch, getState, config) => {
    const { size } = getState().timeline;

    dispatch({ type: IS_REFRESHING });

    try {
      const firstPageResponse = await config.requestsApi.getTimeline({
        size,
        page: 1,
        sort: "oldest",
      });

      const totalHits = firstPageResponse.data.hits.total || 0;
      const lastPageNumber = Math.ceil(totalHits / size);

      let lastPageResponse = null;
      if (lastPageNumber > 1) {
        // Always fetch last page
        lastPageResponse = await config.requestsApi.getTimeline({
          size,
          page: lastPageNumber,
          sort: "oldest",
        });
      }

      let focusedPage = null;
      let focusedPageResponse = null;
      let focusedReplyParentId = null;

      if (focusEventId) {
        // Check if focused event is on first or last page
        const existsOnFirstPage = firstPageResponse.data.hits.hits.some(
          (h) => h.id === focusEventId
        );
        const existsOnLastPage = lastPageResponse?.data.hits.hits.some(
          (h) => h.id === focusEventId
        );

        if (existsOnFirstPage) {
          focusedPage = 1;
        } else if (existsOnLastPage && lastPageNumber > 1) {
          focusedPage = lastPageNumber;
        } else {
          // Fetch focused event info to know which page it's on
          focusedPageResponse = await config.requestsApi.getTimelineFocused(
            focusEventId,
            {
              size,
              sort: "oldest",
            }
          );
          focusedPage = focusedPageResponse?.data?.page;
          focusedReplyParentId = focusedPageResponse?.data?.focused_reply_parent_id;

          if (focusedPageResponse.data.hits.hits.length === 0) {
            dispatch({ type: MISSING_REQUESTED_EVENT });
          }
        }
      }

      dispatch({
        type: SUCCESS,
        payload: {
          firstPageHits: firstPageResponse.data.hits.hits,
          focusedPageHits: focusedPageResponse?.data.hits.hits,
          lastPageHits: lastPageResponse?.data.hits.hits,
          totalHits: totalHits,
          focusedPage: focusedPage,
          pageAfterFocused: focusedPage,
          lastPage: lastPageNumber,
          focusedReplyParentId: focusedReplyParentId,
        },
      });
    } catch (error) {
      dispatch({
        type: HAS_ERROR,
        payload: error,
      });
    }
  };
};

export const fetchNextTimelinePage = (after) => {
  return async (dispatch, getState, config) => {
    const { size, page, pageAfterFocused } = getState().timeline;

    let loadingEvent;
    let pageToLoad;
    if (after === "first") {
      loadingEvent = LOADING_AFTER_FIRST_PAGE;
      pageToLoad = page + 1;
    } else if (after === "focused") {
      loadingEvent = LOADING_AFTER_FOCUSED_PAGE;
      pageToLoad = pageAfterFocused + 1;
    } else {
      throw new Error("Invalid `after` value");
    }

    dispatch({
      type: loadingEvent,
    });

    const response = await config.requestsApi.getTimeline({
      size,
      page: pageToLoad,
      sort: "oldest",
    });

    dispatch({
      type: APPEND_PAGE,
      payload: {
        after,
        newHits: response.data.hits.hits,
        page: pageToLoad,
      },
    });
  };
};

export const fetchLastTimelinePage = () => {
  return async (dispatch, getState, config) => {
    const state = getState();
    const { size, totalHits } = state.timeline;

    if (totalHits === 0) return;

    const lastPageNumber = Math.ceil(totalHits / size);

    // Only fetch last page if there are more than 1 page
    if (lastPageNumber <= 1) return;

    dispatch({ type: IS_REFRESHING });

    try {
      const response = await config.requestsApi.getTimeline({
        size,
        page: lastPageNumber,
        sort: "oldest",
      });

      dispatch({
        type: SUCCESS,
        payload: {
          lastPageHits: response.data.hits.hits,
          totalHits: response.data.hits.total,
          lastPage: lastPageNumber,
        },
      });
    } catch (error) {
      dispatch({ type: HAS_ERROR, payload: error });
    }
  };
};

const timelineReload = (dispatch, getState) => {
  const state = getState();
  const { initialLoading, lastPageRefreshing, error } = state.timeline;
  const { isLoading: isSubmitting } = state.timelineCommentEditor;

  if (error) {
    dispatch(clearTimelineInterval());
  }

  const concurrentRequests = initialLoading || lastPageRefreshing || isSubmitting;
  if (concurrentRequests) return;

  // Fetch only the last page
  dispatch(fetchLastTimelinePage());
};

export const getTimelineWithRefresh = (focusEventId) => {
  return async (dispatch) => {
    dispatch({
      type: IS_LOADING,
    });
    // Fetch both first and last pages
    await dispatch(fetchTimeline(focusEventId));
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
  return () => {
    intervalManager.resetInterval();
  };
};
