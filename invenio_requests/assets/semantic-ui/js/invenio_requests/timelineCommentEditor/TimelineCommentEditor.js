// This file is part of InvenioRequests
// Copyright (C) 2022-2025 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { RichEditor } from "react-invenio-forms";
import React, { useCallback, useEffect, useRef } from "react";
import { CancelButton, SaveButton } from "../components/Buttons";
import { Container, Message, Icon } from "semantic-ui-react";
import PropTypes from "prop-types";
import { i18next } from "@translations/invenio_requests/i18next";
import { RequestEventAvatarContainer } from "../components/RequestsFeed";

const TimelineCommentEditor = ({
  isLoading,
  commentContent,
  storedCommentContent,
  restoreCommentContent,
  setCommentContent,
  appendedCommentContent,
  error,
  submitComment,
  userAvatar,
  canCreateComment,
  autoFocus,
  saveButtonLabel,
  saveButtonIcon,
  onCancel,
}) => {
  useEffect(() => {
    restoreCommentContent();
  }, [restoreCommentContent]);

  const editorRef = useRef(null);
  useEffect(() => {
    if (!appendedCommentContent || !editorRef.current) return;
    // Move the caret to the end of the body and focus the editor.
    // See https://www.tiny.cloud/blog/set-and-get-cursor-position/#h_48266906174501699933284256
    editorRef.current.selection.select(editorRef.current.getBody(), true);
    editorRef.current.selection.collapse(false);
    editorRef.current.focus();
  }, [appendedCommentContent]);

  const onInit = useCallback(
    (_, editor) => {
      editorRef.current = editor;
      if (!autoFocus) return;
      editor.focus();
    },
    [autoFocus]
  );

  return (
    <div className="timeline-comment-editor-container">
      {error && <Message negative>{error}</Message>}
      {!canCreateComment && (
        <Message icon warning>
          <Icon name="info circle" size="large" />
          <Message.Content>
            {i18next.t("Adding or editing comments is now locked.")}
          </Message.Content>
        </Message>
      )}
      <div className="flex">
        <RequestEventAvatarContainer
          src={userAvatar}
          className="tablet computer only rel-mr-1"
          disabled={!canCreateComment}
        />
        <Container fluid className="ml-0-mobile mr-0-mobile fluid-mobile">
          <RichEditor
            inputValue={commentContent}
            // initialValue is not allowed to change, so we use `storedCommentContent` which is set at most once
            initialValue={storedCommentContent}
            onEditorChange={(_, editor) => {
              setCommentContent(editor.getContent());
            }}
            onInit={onInit}
            minHeight={150}
            disabled={!canCreateComment}
          />
        </Container>
      </div>
      <div className="text-align-right rel-mt-1">
        {onCancel && (
          <CancelButton
            size="medium"
            className="mr-10"
            onClick={onCancel}
            disabled={isLoading}
          />
        )}
        <SaveButton
          icon={saveButtonIcon}
          size="medium"
          content={saveButtonLabel}
          loading={isLoading}
          onClick={() => submitComment(commentContent, "html")}
          disabled={!canCreateComment}
        />
      </div>
    </div>
  );
};

TimelineCommentEditor.propTypes = {
  commentContent: PropTypes.string,
  storedCommentContent: PropTypes.string,
  appendedCommentContent: PropTypes.string,
  isLoading: PropTypes.bool,
  setCommentContent: PropTypes.func.isRequired,
  error: PropTypes.string,
  submitComment: PropTypes.func.isRequired,
  restoreCommentContent: PropTypes.func.isRequired,
  userAvatar: PropTypes.string,
  canCreateComment: PropTypes.bool,
  autoFocus: PropTypes.bool,
  saveButtonLabel: PropTypes.string,
  saveButtonIcon: PropTypes.string,
  onCancel: PropTypes.func,
};

TimelineCommentEditor.defaultProps = {
  commentContent: "",
  storedCommentContent: null,
  appendedCommentContent: "",
  isLoading: false,
  error: "",
  userAvatar: "",
  canCreateComment: true,
  autoFocus: false,
  saveButtonLabel: i18next.t("Comment"),
  saveButtonIcon: "send",
  onCancel: null,
};

export default TimelineCommentEditor;
