import { connect } from "react-redux";
import TimelineCommentRepliesComponent from "./TimelineCommentReplies.js";
import { selectCommentReplies, selectCommentRepliesStatus } from "./state/reducer.js";
import {
  appendEventContent,
  clearDraft,
  IS_SUBMITTING,
  loadOlderReplies,
  REPLY_DELETE_COMMENT,
  REPLY_RESTORE_DRAFT_CONTENT,
  REPLY_SET_DRAFT_CONTENT,
  REPLY_UPDATE_COMMENT,
  setInitialReplies,
  setIsReplying,
  submitReply,
} from "./state/actions.js";
import {
  restoreEventContent,
  setEventContent,
} from "../timelineCommentEditor/state/actions.js";
import {
  deleteComment,
  updateComment,
} from "../timelineCommentEventControlled/state/actions.js";

const mapStateToProps = (state, ownProps) => {
  const { parentRequestEvent } = ownProps;
  const commentReplies = selectCommentReplies(
    state.timelineReplies,
    parentRequestEvent.id
  );
  const status = selectCommentRepliesStatus(
    state.timelineReplies,
    parentRequestEvent.id
  );
  return {
    commentReplies,
    ...status,
    focusedReplyParentId: state.timeline.focusedReplyParentId,
  };
};

const mapDispatchToProps = {
  loadOlderReplies,
  setInitialReplies,
  setIsReplying,
  setCommentContent: (content, parentRequestEventId) =>
    setEventContent(content, parentRequestEventId, REPLY_SET_DRAFT_CONTENT),
  restoreCommentContent: (parentRequestEventId) =>
    restoreEventContent(parentRequestEventId, REPLY_RESTORE_DRAFT_CONTENT),
  appendCommentContent: (content, parentRequestEventId) =>
    appendEventContent(parentRequestEventId, content),
  submitReply,
  updateComment: (payload, parentRequestEventId) =>
    updateComment({
      ...payload,
      parentRequestEventId,
      successEvent: REPLY_UPDATE_COMMENT,
      loadingEvent: IS_SUBMITTING,
    }),
  deleteComment: (payload, parentRequestEventId) =>
    deleteComment({
      ...payload,
      parentRequestEventId,
      successEvent: REPLY_DELETE_COMMENT,
      loadingEvent: IS_SUBMITTING,
    }),
  clearDraft,
};

export const TimelineCommentReplies = connect(
  mapStateToProps,
  mapDispatchToProps
)(TimelineCommentRepliesComponent);
