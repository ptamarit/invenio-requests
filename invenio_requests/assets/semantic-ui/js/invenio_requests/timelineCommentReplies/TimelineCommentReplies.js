// This file is part of InvenioRequests
// Copyright (C) 2025 CERN.
//
// Invenio Requests is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import Overridable from "react-overridable";
import React, { Component } from "react";
import PropTypes from "prop-types";
import { Button, Divider, Icon } from "semantic-ui-react";
import FakeInput from "../components/FakeInput";
import { i18next } from "@translations/invenio_requests/i18next";
import TimelineCommentEditor from "../timelineCommentEditor/TimelineCommentEditor";
import TimelineCommentEventControlled from "../timelineCommentEventControlled/TimelineCommentEventControlled.js";
import { DeleteConfirmationModal } from "../components/modals/DeleteConfirmationModal";

class TimelineCommentReplies extends Component {
  constructor() {
    super();
    this.state = {
      isExpanded: true,
      deleteModalAction: undefined,
    };
  }

  componentDidMount() {
    const { setInitialReplies, parentRequestEvent } = this.props;
    setInitialReplies(parentRequestEvent);
  }

  onRepliesClick = () => {
    const { isExpanded } = this.state;
    this.setState({ isExpanded: !isExpanded });
  };

  onFakeInputActivate = (value) => {
    const { setIsReplying, parentRequestEvent } = this.props;
    setIsReplying(parentRequestEvent.id, true);
  };

  restoreCommentContent = () => {
    const { restoreCommentContent, parentRequestEvent } = this.props;
    restoreCommentContent(parentRequestEvent.id);
  };

  setCommentContent = (content) => {
    const { setCommentContent, parentRequestEvent } = this.props;
    setCommentContent(content, parentRequestEvent.id);
  };

  appendCommentContent = (content) => {
    const { appendCommentContent, parentRequestEvent, setIsReplying } = this.props;
    setIsReplying(parentRequestEvent.id, true);
    appendCommentContent(content, parentRequestEvent.id);
  };

  submitReply = (content, format) => {
    const { submitReply, parentRequestEvent } = this.props;
    submitReply(parentRequestEvent, content, format);
  };

  onLoadMoreClick = () => {
    const { loadOlderReplies, parentRequestEvent } = this.props;
    loadOlderReplies(parentRequestEvent);
  };

  onDeleteModalOpen = (action) => {
    this.setState({ deleteModalAction: action });
  };

  deleteComment = (payload) => {
    const { deleteComment, parentRequestEvent } = this.props;
    deleteComment(payload, parentRequestEvent.id);
  };

  updateComment = (payload) => {
    const { updateComment, parentRequestEvent } = this.props;
    updateComment(payload, parentRequestEvent.id);
  };

  onCancelClick = () => {
    const { clearDraft, parentRequestEvent, setIsReplying } = this.props;
    setIsReplying(parentRequestEvent.id, false);
    clearDraft(parentRequestEvent);
  };

  render() {
    const {
      commentReplies,
      userAvatar,
      draftContent,
      storedDraftContent,
      appendedDraftContent,
      totalReplyCount,
      submitting,
      error,
      hasMore,
      loading,
      isReplying,
      pageSize,
    } = this.props;
    const { isExpanded, deleteModalAction } = this.state;
    const hasReplies = totalReplyCount > 0;

    const notYetLoadedCommentCount = totalReplyCount - commentReplies.length;
    const nextLoadSize =
      notYetLoadedCommentCount >= pageSize ? pageSize : notYetLoadedCommentCount;

    return (
      <div className="requests-reply-container">
        {hasReplies && (
          <>
            <Button
              size="tiny"
              onClick={this.onRepliesClick}
              className="text-only requests-reply-expand"
            >
              <Icon
                name={`caret ${isExpanded ? "down" : "right"}`}
                className="requests-reply-caret"
              />
              {i18next.t("Replies")}
              <span className="requests-reply-count ml-5">{totalReplyCount}</span>
            </Button>

            {(isExpanded || isReplying) && (
              <div>
                {hasMore && (
                  <Button
                    size="tiny"
                    onClick={this.onLoadMoreClick}
                    className="text-only requests-reply-load-more"
                    disabled={loading}
                  >
                    {i18next.t("Load {{count}} more", { count: nextLoadSize })}
                  </Button>
                )}
                {commentReplies.map((c) => (
                  <TimelineCommentEventControlled
                    key={c.id}
                    event={c}
                    isReply
                    openConfirmModal={this.onDeleteModalOpen}
                    updateComment={this.updateComment}
                    deleteComment={this.deleteComment}
                    appendCommentContent={this.appendCommentContent}
                    allowCopyLink={false}
                  />
                ))}
                <Divider />
              </div>
            )}
          </>
        )}

        <DeleteConfirmationModal
          open={!!deleteModalAction}
          action={deleteModalAction}
          onOpen={() => {}}
          onClose={() => this.setState({ deleteModalAction: undefined })}
        />

        {!isReplying ? (
          <FakeInput
            placeholder={i18next.t("Write a reply")}
            userAvatar={userAvatar}
            onActivate={this.onFakeInputActivate}
            className={!hasReplies || !isExpanded ? "mt-10" : undefined}
          />
        ) : (
          <TimelineCommentEditor
            // We must declare these as static (non-inline) functions to avoid re-rendering
            restoreCommentContent={this.restoreCommentContent}
            setCommentContent={this.setCommentContent}
            submitComment={this.submitReply}
            commentContent={draftContent}
            storedCommentContent={storedDraftContent}
            appendedCommentContent={appendedDraftContent}
            userAvatar={userAvatar}
            isLoading={submitting}
            error={error}
            saveButtonLabel={i18next.t("Reply")}
            saveButtonIcon="reply"
            onCancel={this.onCancelClick}
            // eslint-disable-next-line jsx-a11y/no-autofocus
            autoFocus
          />
        )}
      </div>
    );
  }
}

TimelineCommentReplies.propTypes = {
  commentReplies: PropTypes.array.isRequired,
  parentRequestEvent: PropTypes.object.isRequired,
  loadOlderReplies: PropTypes.func.isRequired,
  userAvatar: PropTypes.string,
  setCommentContent: PropTypes.func.isRequired,
  restoreCommentContent: PropTypes.func.isRequired,
  appendCommentContent: PropTypes.func.isRequired,
  submitting: PropTypes.bool.isRequired,
  error: PropTypes.string,
  draftContent: PropTypes.string.isRequired,
  storedDraftContent: PropTypes.string.isRequired,
  appendedDraftContent: PropTypes.string.isRequired,
  submitReply: PropTypes.func.isRequired,
  setInitialReplies: PropTypes.func.isRequired,
  hasMore: PropTypes.bool.isRequired,
  updateComment: PropTypes.func.isRequired,
  deleteComment: PropTypes.func.isRequired,
  clearDraft: PropTypes.func.isRequired,
  loading: PropTypes.bool.isRequired,
  totalReplyCount: PropTypes.number.isRequired,
  isReplying: PropTypes.bool.isRequired,
  setIsReplying: PropTypes.func.isRequired,
  pageSize: PropTypes.number.isRequired,
};

TimelineCommentReplies.defaultProps = {
  userAvatar: "",
  error: null,
};

export default Overridable.component(
  "InvenioRequests.Timeline.CommentReplies",
  TimelineCommentReplies
);
