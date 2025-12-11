// This file is part of InvenioRequests
// Copyright (C) 2022 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import PropTypes from "prop-types";
import { ButtonGroup, Button, Popup } from "semantic-ui-react";
import { i18next } from "@translations/invenio_requests/i18next";
import { humanReadableBytes } from "react-invenio-forms";

function getCookie(cname) {
  let name = cname + "=";
  let decodedCookie = decodeURIComponent(document.cookie);
  let ca = decodedCookie.split(";");
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == " ") {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}

// TODO: Use nested_links_item
function getRequestId() {
  const prefix = "/requests/";
  const url = window.location.href;
  const index = url.indexOf(prefix);
  const start = index + prefix.length;
  const end = start + 36;
  return url.substring(start, end);
}

export const TimelineEventBody = ({ content, format, quote, files }) => {
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

  const onQuoteClick = useCallback(() => {
    if (!selectionRange) return;
    quote(selectionRange.toString());
    window.getSelection().removeAllRanges();
  }, [selectionRange, quote]);

  useEffect(() => {
    window.invenio?.onSearchResultsRendered();
  }, []);

  const contentResult = (
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
      <Button
        onClick={onQuoteClick}
        icon="quote left"
        content={i18next.t("Quote")}
        size="small"
        basic
      />
    </Popup>
  );

  const filesList = files.map((file) => (
    <ButtonGroup key={file.key} floated='left' className="mr-10 mt-10">
      <Button basic color='grey' icon='file' content={`${file.original_filename} (${humanReadableBytes(parseInt(file.size, 10), true)})`} as='a' href={`/api/requests/${getRequestId()}/files/${file.key}/content`} />
      <Button icon='linkify' title="Copy link" onClick={() => this.copyLink(file.key)} />
    </ButtonGroup>
  ))

  return <>{contentResult}<small>Files:</small>{filesList}</>;
};

TimelineEventBody.propTypes = {
  content: PropTypes.string,
  format: PropTypes.string,
  quote: PropTypes.func.isRequired,
  files: PropTypes.array,
};

TimelineEventBody.defaultProps = {
  content: "",
  format: "",
  files: [],
};
