// This file is part of InvenioRequests
// Copyright (C) 2022-2025 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { connect } from "react-redux";
import {
  submitComment,
  setEventContent,
  restoreEventContent,
  PARENT_SET_DRAFT_CONTENT,
  PARENT_RESTORE_DRAFT_CONTENT,
} from "./state/actions";
import TimelineCommentEditorComponent from "./TimelineCommentEditor";

const mapDispatchToProps = {
  submitComment,
  setCommentContent: (content) =>
    setEventContent(content, undefined, PARENT_SET_DRAFT_CONTENT),
  restoreCommentContent: () =>
    restoreEventContent(undefined, PARENT_RESTORE_DRAFT_CONTENT),
};

const mapStateToProps = (state) => ({
  isLoading: state.timelineCommentEditor.isLoading,
  error: state.timelineCommentEditor.error,
  commentContent: state.timelineCommentEditor.commentContent,
  storedCommentContent: state.timelineCommentEditor.storedCommentContent,
  appendedCommentContent: state.timelineCommentEditor.appendedCommentContent,
});

export const TimelineCommentEditor = connect(
  mapStateToProps,
  mapDispatchToProps
)(TimelineCommentEditorComponent);
