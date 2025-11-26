// This file is part of InvenioRequests
// Copyright (C) 2022 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import EventWithStateComponent from "./TimelineCommentEventControlled";
import { connect } from "react-redux";
import { updateComment, deleteComment } from "./state/actions";
import {
  IS_REFRESHING,
  PARENT_DELETED_COMMENT,
  PARENT_UPDATED_COMMENT,
} from "../timeline/state/actions";
import {
  appendEventContent,
  PARENT_APPEND_DRAFT_CONTENT,
} from "../timelineCommentEditor/state/actions";
import { REPLY_APPEND_DRAFT_CONTENT } from "../timelineCommentReplies/state/actions";

const mapDispatchToProps = (dispatch, ownProps) => ({
  updateComment: async (payload) =>
    dispatch(
      updateComment({
        ...payload,
        successEvent: PARENT_UPDATED_COMMENT,
        loadingEvent: IS_REFRESHING,
      })
    ),
  deleteComment: async (payload) =>
    dispatch(
      deleteComment({
        ...payload,
        successEvent: PARENT_DELETED_COMMENT,
        loadingEvent: IS_REFRESHING,
      })
    ),
  appendCommentContent: (content, asReply) =>
    dispatch(
      appendEventContent(
        ownProps.event.id,
        content,
        asReply ? REPLY_APPEND_DRAFT_CONTENT : PARENT_APPEND_DRAFT_CONTENT
      )
    ),
});

export const TimelineCommentEventControlled = connect(
  null,
  mapDispatchToProps
)(EventWithStateComponent);
