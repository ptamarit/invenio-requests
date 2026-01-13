// This file is part of InvenioRequests
// Copyright (C) 2022 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import PropTypes from "prop-types";
import { Button, Popup, ButtonGroup } from "semantic-ui-react";
import { i18next } from "@translations/invenio_requests/i18next";

export const TimelineEventBody = ({ payload, quoteReply, collapsedHeight = 200 }) => {
  const ref = useRef(null);
  const [selectionRange, setSelectionRange] = useState(null);
  const [expanded, setExpanded] = useState(false);
  const [maxHeight, setMaxHeight] = useState(collapsedHeight);
  const [isOverflowing, setIsOverflowing] = useState(false);

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

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const fullHeight = el.scrollHeight;
    const overflowing = fullHeight > collapsedHeight;

    setIsOverflowing(overflowing);
    setMaxHeight(expanded || !overflowing ? fullHeight : collapsedHeight);
  }, [ref, expanded, collapsedHeight]);

  const toggleCollapsed = () => {
    const el = ref.current;
    if (!el) return;

    setMaxHeight(expanded ? collapsedHeight : el.scrollHeight);
    setExpanded((prev) => !prev);
  };

  const tooltipOffset = useMemo(() => {
    if (!selectionRange) return null;

    const selectionRect = selectionRange.getBoundingClientRect();
    const refRect = ref.current.getBoundingClientRect();

    // Offset set as [x, y] from the reference position.
    // E.g. `top left` is relative to [0,0] but `top center` is relative to [{center}, 0]
    return [selectionRect.x - refRect.x, -(selectionRect.y - refRect.y)];
  }, [selectionRange]);

  const onQuoteClick = useCallback(() => {
    if (!selectionRange || !quoteReply) return;
    const selectionString = selectionRange.toString();
    quoteReply(selectionString);
    window.getSelection().removeAllRanges();
  }, [selectionRange, quoteReply]);

  useEffect(() => {
    window.invenio?.onSearchResultsRendered();
  }, []);

  const { format, content, event } = payload;

  if (!quoteReply) {
    return (
      <span
        ref={ref}
        className={`collapsible-comment ${
          isOverflowing && !expanded ? "overflowing" : ""
        }`}
        style={{ maxHeight }}
      >
        {content}
        {isOverflowing && !expanded && (
          <button type="button" className="show-more" onClick={toggleCollapsed}>
            Show more
          </button>
        )}
      </span>
    );
  }

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
        <span
          ref={ref}
          className={`collapsible-comment ${
            isOverflowing && !expanded ? "overflowing" : ""
          }`}
          style={{ maxHeight }}
        >
          {format === "html" ? (
            <span dangerouslySetInnerHTML={{ __html: content }} />
          ) : (
            content
          )}
          {isOverflowing && !expanded && (
            <button type="button" className="show-more" onClick={toggleCollapsed}>
              Show more
            </button>
          )}
        </span>
      }
      basic
    >
      <ButtonGroup basic size="small">
        <Button
          onClick={onQuoteClick}
          icon="reply"
          content={i18next.t("Quote reply")}
        />
      </ButtonGroup>
    </Popup>
  );
};

TimelineEventBody.propTypes = {
  payload: PropTypes.object,
  quoteReply: PropTypes.func,
  collapsedHeight: PropTypes.number,
};

TimelineEventBody.defaultProps = {
  payload: {},
  quoteReply: null,
  collapsedHeight: 200,
};
