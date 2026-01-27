import React, { Component } from "react";
import TimelineFeedComponent from "../timeline/TimelineFeed";
import PropTypes from "prop-types";
import { getEventIdFromUrl } from "../timelineEvents/utils";

class TimelineFeedParent extends Component {
  componentDidMount() {
    const { getTimelineWithRefresh } = this.props;
    getTimelineWithRefresh(getEventIdFromUrl());
  }

  componentWillUnmount() {
    const { timelineStopRefresh } = this.props;
    timelineStopRefresh();
  }

  render() {
    const { getTimelineWithRefresh: _, timelineStopRefresh: __, ...props } = this.props;
    return <TimelineFeedComponent {...props} />;
  }
}

TimelineFeedParent.propTypes = {
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
};

TimelineFeedParent.defaultProps = {
  timeline: null,
  error: null,
  isSubmitting: false,
  userAvatar: "",
  warning: null,
  parentRequestEvent: null,
};

export default TimelineFeedParent;
