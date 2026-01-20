// This file is part of InvenioRequests
// Copyright (C) 2022-2025 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { connect } from "react-redux";
import {
  submitComment,
  setEventContent,
  setEventFiles,
  restoreEventContent,
  restoreEventFiles,
  PARENT_SET_DRAFT_CONTENT,
  PARENT_RESTORE_DRAFT_CONTENT,
  PARENT_SET_DRAFT_FILES,
  PARENT_RESTORE_DRAFT_FILES,
} from "./state/actions";
import TimelineCommentEditorComponent from "./TimelineCommentEditor";

const mapDispatchToProps = {
  submitComment,
  setCommentContent: (content) =>
    setEventContent(content, null, PARENT_SET_DRAFT_CONTENT),
  restoreCommentContent: () => restoreEventContent(null, PARENT_RESTORE_DRAFT_CONTENT),
  setCommentFiles: (files) => setEventFiles(files, null, PARENT_SET_DRAFT_FILES),
  restoreCommentFiles: () => restoreEventFiles(null, PARENT_RESTORE_DRAFT_FILES),
};

const mapStateToProps = (state) => ({
  isLoading: state.timelineCommentEditor.isLoading,
  error: state.timelineCommentEditor.error,
  commentContent: state.timelineCommentEditor.commentContent,
  storedCommentContent: state.timelineCommentEditor.storedCommentContent,
  appendedCommentContent: state.timelineCommentEditor.appendedCommentContent,
  files: state.timelineCommentEditor.files,
});

export const TimelineCommentEditor = connect(
  mapStateToProps,
  mapDispatchToProps
)(TimelineCommentEditorComponent);
