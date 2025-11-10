// This file is part of InvenioRequests
// Copyright (C) 2022-2025 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { connect } from "react-redux";
import { submitComment, setEventContent, restoreEventContent } from "./state/actions";
import TimelineCommentEditorComponent from "./TimelineCommentEditor";

const mapDispatchToProps = {
  submitComment,
  setCommentContent: setEventContent,
  restoreCommentContent: restoreEventContent,
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
