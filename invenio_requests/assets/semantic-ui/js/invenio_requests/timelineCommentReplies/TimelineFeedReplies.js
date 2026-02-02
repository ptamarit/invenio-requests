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
};

export default TimelineFeedReplies;
