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
import { InvenioRequestFilesApi } from "../api/InvenioRequestFilesApi";

const TimelineCommentEditor = ({
  isLoading,
  commentContent,
  storedCommentContent,
  restoreCommentContent,
  setCommentContent,
  appendedCommentContent,
  files,
  restoreCommentFiles,
  setCommentFiles,
  error,
  submitComment,
  userAvatar,
  canCreateComment,
  autoFocus,
  saveButtonLabel,
  saveButtonIcon,
  onCancel,
  disabled,
  request,
}) => {
  useEffect(() => {
    restoreCommentContent();
  }, [restoreCommentContent]);

  useEffect(() => {
    restoreCommentFiles();
  }, [restoreCommentFiles]);

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

  const onFileUpload = async (filename, payload, options) => {
    const client = new InvenioRequestFilesApi();
    return await client.uploadFile(request.id, filename, payload, options);
  };

  const onFileDelete = async (file) => {
    const client = new InvenioRequestFilesApi();
    await client.deleteFile(request.id, file.key);
  };

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
            onEditorChange={(event, editor) => {
              setCommentContent(editor.getContent());
            }}
            onInit={onInit}
            minHeight={150}
            disabled={!canCreateComment || disabled}
            files={files}
            onFilesChange={(files) => {
              setCommentFiles(files);
            }}
            onFileUpload={onFileUpload}
            onFileDelete={onFileDelete}
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
          onClick={() => submitComment(commentContent, "html", files)}
          disabled={!canCreateComment}
        />
      </div>
    </div>
  );
};

TimelineCommentEditor.propTypes = {
  commentContent: PropTypes.string,
  files: PropTypes.array,
  restoreCommentFiles: PropTypes.func.isRequired,
  setCommentFiles: PropTypes.func.isRequired,
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
  disabled: PropTypes.bool,
  request: PropTypes.object.isRequired,
};

TimelineCommentEditor.defaultProps = {
  commentContent: "",
  files: [],
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
  disabled: false,
};

export default TimelineCommentEditor;
