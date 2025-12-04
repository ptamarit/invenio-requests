// This file is part of InvenioRequests
// Copyright (C) 2022-2025 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { RichEditorWithFiles } from "react-invenio-forms";
import React, { useEffect, useState } from "react";
import { SaveButton } from "../components/Buttons";
import { Container, Message } from "semantic-ui-react";
import PropTypes from "prop-types";
import { i18next } from "@translations/invenio_requests/i18next";
import { RequestEventAvatarContainer } from "../components/RequestsFeed";

const TimelineCommentEditor = ({
  isLoading,
  commentContent,
  storedCommentContent,
  restoreCommentContent,
  setCommentContent,
  error,
  submitComment,
  userAvatar,
}) => {
  useEffect(() => {
    restoreCommentContent();
  }, [restoreCommentContent]);
  
  const [files, setFiles] = useState([]);
  
  return (
    <div className="timeline-comment-editor-container">
      {error && <Message negative>{error}</Message>}
      <div className="flex">
        <RequestEventAvatarContainer
          src={userAvatar}
          className="tablet computer only rel-mr-1"
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
        />
      </div>
    </div>
  );
};

TimelineCommentEditor.propTypes = {
  commentContent: PropTypes.string,
  storedCommentContent: PropTypes.string,
  isLoading: PropTypes.bool,
  setCommentContent: PropTypes.func.isRequired,
  error: PropTypes.string,
  submitComment: PropTypes.func.isRequired,
  restoreCommentContent: PropTypes.func.isRequired,
  userAvatar: PropTypes.string,
};

TimelineCommentEditor.defaultProps = {
  commentContent: "",
  storedCommentContent: null,
  isLoading: false,
  error: "",
  userAvatar: "",
};

export default TimelineCommentEditor;
