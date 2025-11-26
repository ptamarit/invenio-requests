// This file is part of InvenioRequests
// Copyright (C) 2022 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import PropTypes from "prop-types";
import { Button, Popup, ButtonGroup } from "semantic-ui-react";
import { i18next } from "@translations/invenio_requests/i18next";

export const TimelineEventBody = ({ payload, quote, quoteReply }) => {
  const ref = useRef(null);
  const [selectionRange, setSelectionRange] = useState(null);

  useEffect(() => {
    if (ref.current === null) return;

    const onSelectionChange = () => {
      const selection = window.getSelection();

      // anchorNode is where the user started dragging the mouse,
      // focusNode is where they finished. We make sure both nodes
      // are contained by the ref so we are sure that 100% of the selection
      // is within this comment event.
      const selectionIsContainedByRef =
        ref.current.contains(selection.anchorNode) &&
        ref.current.contains(selection.focusNode);

      if (
        !selectionIsContainedByRef ||
        selection.rangeCount === 0 ||
        // A "Caret" type e.g. should not trigger a tooltip
        selection.type !== "Range"
      ) {
        setSelectionRange(null);
        return;
      }

      setSelectionRange(selection.getRangeAt(0));
    };

    document.addEventListener("selectionchange", onSelectionChange);
    return () => document.removeEventListener("selectionchange", onSelectionChange);
  }, [ref]);

  const tooltipOffset = useMemo(() => {
    if (!selectionRange) return null;

    const selectionRect = selectionRange.getBoundingClientRect();
    const refRect = ref.current.getBoundingClientRect();

    // Offset set as [x, y] from the reference position.
    // E.g. `top left` is relative to [0,0] but `top center` is relative to [{center}, 0]
    return [selectionRect.x - refRect.x, -(selectionRect.y - refRect.y)];
  }, [selectionRange]);

  const onQuoteClick = useCallback(
    (reply) => {
      if (!selectionRange) return;
      const selectionString = selectionRange.toString();
      if (reply) {
        quoteReply(selectionString);
      } else {
        quote(selectionString);
      }
      window.getSelection().removeAllRanges();
    },
    [selectionRange, quote, quoteReply]
  );

  useEffect(() => {
    window.invenio?.onSearchResultsRendered();
  }, []);

  const { format, content, event } = payload;

  if (event === "comment_deleted") {
    return (
      <span ref={ref}>
        <p className="requests-event-body-deleted">
          {i18next.t("Comment was deleted.")}
        </p>
      </span>
    );
  }

  return (
    <Popup
      eventsEnabled={false}
      open={!!tooltipOffset}
      offset={tooltipOffset}
      position="top left"
      className="requests-event-body-popup"
      trigger={
        <span ref={ref}>
          {format === "html" ? (
            <span dangerouslySetInnerHTML={{ __html: content }} />
          ) : (
            content
          )}
        </span>
      }
      basic
    >
      <ButtonGroup basic size="small">
        {quote && (
          <Button
            onClick={() => onQuoteClick(false)}
            icon="quote left"
            content={i18next.t("Quote")}
          />
        )}
        {quoteReply && (
          <Button
            onClick={() => onQuoteClick(true)}
            icon="reply"
            content={i18next.t("Quote reply")}
          />
        )}
      </ButtonGroup>
    </Popup>
  );
};

TimelineEventBody.propTypes = {
  payload: PropTypes.object,
  quote: PropTypes.func,
  quoteReply: PropTypes.func,
};

TimelineEventBody.defaultProps = {
  payload: {},
  quote: null,
  quoteReply: null,
};
