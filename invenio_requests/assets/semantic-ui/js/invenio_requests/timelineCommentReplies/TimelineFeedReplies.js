import React, { Component } from "react";
import TimelineFeedComponent from "../timeline/TimelineFeed";
import PropTypes from "prop-types";
import { getEventIdFromUrl } from "../timelineEvents/utils";

class TimelineFeedReplies extends Component {
  componentDidMount() {
    const { setInitialReplies } = this.props;
    setInitialReplies(getEventIdFromUrl());
  }

  render() {
    const { ...props } = this.props;
    return <TimelineFeedComponent {...props} />;
  }
}

TimelineFeedReplies.propTypes = {
  setInitialReplies: PropTypes.func.isRequired,
  getTimelineWithRefresh: PropTypes.func.isRequired,
  timelineStopRefresh: PropTypes.func.isRequired,
  fetchPage: PropTypes.func.isRequired,
  error: PropTypes.string,
  isSubmitting: PropTypes.bool,
  size: PropTypes.number.isRequired,
  userAvatar: PropTypes.string,
  request: PropTypes.object.isRequired,
  permissions: PropTypes.object.isRequired,
  initialLoading: PropTypes.bool.isRequired,
  warning: PropTypes.string,
  parentRequestEvent: PropTypes.object,
  totalHits: PropTypes.number.isRequired,
};

TimelineFeedReplies.defaultProps = {
  timeline: null,
  error: null,
  isSubmitting: false,
  userAvatar: "",
  warning: null,
  parentRequestEvent: null,
};

export default TimelineFeedReplies;
