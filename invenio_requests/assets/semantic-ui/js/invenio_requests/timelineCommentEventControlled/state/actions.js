// This file is part of InvenioRequests
// Copyright (C) 2022 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { clearTimelineInterval } from "../../timeline/state/actions";
import { payloadSerializer } from "../../api/serializers";

export const updateComment = ({
  content,
  format,
  parentRequestEventId,
  requestEvent,
  successEvent,
  loadingEvent,
}) => {
  return async (dispatch, getState, config) => {
    dispatch(clearTimelineInterval());
    const commentsApi = config.requestEventsApi(requestEvent.links);

    const payload = payloadSerializer(content, format);

    dispatch({
      type: loadingEvent,
      payload: {
        parentRequestEventId: parentRequestEventId,
      },
    });

    const response = await commentsApi.updateComment(payload);

    dispatch({
      type: successEvent,
      payload: {
        updatedComment: response.data,
        parentRequestEventId: parentRequestEventId,
      },
    });

    return response.data;
  };
};

export const deleteComment = ({
  parentRequestEventId,
  requestEvent,
  loadingEvent,
  successEvent,
}) => {
  return async (dispatch, getState, config) => {
    dispatch(clearTimelineInterval());
    const commentsApi = config.requestEventsApi(requestEvent.links);

    dispatch({
      type: loadingEvent,
      payload: {
        parentRequestEventId: parentRequestEventId,
      },
    });

    const response = await commentsApi.deleteComment();

    dispatch({
      type: successEvent,
      payload: {
        deletedCommentId: requestEvent.id,
        parentRequestEventId: parentRequestEventId,
      },
    });

    return response.data;
  };
};
