// This file is part of InvenioRequests
// Copyright (C) 2022 CERN.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React from "react";
import PropTypes from "prop-types";
import { ButtonGroup, Button } from 'semantic-ui-react'

export const TimelineEventBody = ({ content, format, files }) => {
  const contentResult = format === "html" ? (
    <span dangerouslySetInnerHTML={{ __html: content }} />
  ) : (
    content
  );

  const filesList = files.map((file) => (
    <ButtonGroup key={file.key} floated='left' className="mr-10 mt-10">
      <Button basic color='grey' icon='file' content={`${file.original_filename} (12.3 MB)`} as='a' href={`/api/requests/TODOreqID/files/${file.key}/content`} />
      <Button icon='linkify' title="Copy link" onClick={() => this.copyLink(file.key)} />
    </ButtonGroup>
  ))

  return <>{contentResult}<small>Files:</small>{filesList}</>;
};

TimelineEventBody.propTypes = {
  content: PropTypes.string,
  format: PropTypes.string,
  files: PropTypes.array,
};

TimelineEventBody.defaultProps = {
  content: "",
  format: "",
  files: [],
};
