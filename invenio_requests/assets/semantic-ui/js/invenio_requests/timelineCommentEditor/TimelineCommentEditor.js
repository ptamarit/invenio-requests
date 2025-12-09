// This file is part of InvenioRequests
// Copyright (C) 2022-2025 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React, { useEffect, useState, useRef } from "react";
import { RichEditorWithFiles } from "react-invenio-forms";
import { SaveButton } from "../components/Buttons";
import { Container, Message, Icon } from "semantic-ui-react";
import PropTypes from "prop-types";
import { i18next } from "@translations/invenio_requests/i18next";
import { RequestEventAvatarContainer } from "../components/RequestsFeed";

const TimelineCommentEditor = ({
  isLoading,
  commentContent,
  files: initialFiles,
  storedCommentContent,
  restoreCommentContent,
  setCommentContent,
  appendedCommentContent,
  error,
  submitComment,
  userAvatar,
  canCreateComment,
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

  const [files, setFiles] = useState(initialFiles);

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
          {/* TODO: This is the comment at the bottom of the timeline. */}
          {/* TODO: Inject the request ID here for file uploading? */}
          <small>TimelineCommentEditor.js</small>
          <RichEditorWithFiles
            inputValue={commentContent}
            // initialValue is not allowed to change, so we use `storedCommentContent` which is set at most once
            initialValue={storedCommentContent}
            files={files}
            setFiles={setFiles}
            onEditorChange={(event, editor) => {
              // TODO: Store the list of files too, and not only on editor change, but also on files change.
              setCommentContent(editor.getContent());
              // setCommentContent({
              //   content: editor.getContent(),
              //   files: editor.getFiles(),
              // })
            }}
            minHeight={150}
            onInit={(_, editor) => (editorRef.current = editor)}
            disabled={!canCreateComment}
            // editorConfig={{}}
          />
        </Container>
      </div>
      <div className="text-align-right rel-mt-1">
        <SaveButton
          icon="send"
          size="medium"
          content={i18next.t("Comment")}
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
  storedCommentContent: PropTypes.string,
  appendedCommentContent: PropTypes.string,
  isLoading: PropTypes.bool,
  setCommentContent: PropTypes.func.isRequired,
  error: PropTypes.string,
  submitComment: PropTypes.func.isRequired,
  restoreCommentContent: PropTypes.func.isRequired,
  userAvatar: PropTypes.string,
  canCreateComment: PropTypes.bool,
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
};

export default TimelineCommentEditor;
