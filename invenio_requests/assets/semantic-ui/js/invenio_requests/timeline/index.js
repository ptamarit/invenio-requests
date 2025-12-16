// This file is part of InvenioRequests
// Copyright (C) 2022 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { connect } from "react-redux";
import {
  getTimelineWithRefresh,
  clearTimelineInterval,
  appendPage,
  setLoadingForLoadMore,
  fetchNextTimelinePage,
} from "./state/actions";
import TimelineFeedComponent from "./TimelineFeed";

const mapDispatchToProps = (dispatch) => ({
  getTimelineWithRefresh: (includeEventId) =>
    dispatch(getTimelineWithRefresh(includeEventId)),
  timelineStopRefresh: () => dispatch(clearTimelineInterval()),
  fetchNextTimelinePage: (after) => dispatch(fetchNextTimelinePage(after)),
  appendPage: (payload) => dispatch(appendPage(payload)),
  setLoadingForLoadMore: (type) => dispatch(setLoadingForLoadMore(type)),
});

const mapStateToProps = (state) => ({
  initialLoading: state.timeline.initialLoading,
  lastPageRefreshing: state.timeline.lastPageRefreshing,
  timeline: state.timeline,
  error: state.timeline.error,
  isSubmitting: state.timelineCommentEditor.isLoading,
  size: state.timeline.size,
  page: state.timeline.page,
  warning: state.timeline.warning,
});

export const Timeline = connect(
  mapStateToProps,
  mapDispatchToProps
)(TimelineFeedComponent);
