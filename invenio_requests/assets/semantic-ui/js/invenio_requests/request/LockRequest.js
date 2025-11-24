// This file is part of InvenioRequests
// Copyright (C) 2025 CERN.
//
// Invenio Requests is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React from "react";
import { Divider } from "semantic-ui-react";
import {
  RequestLockButton,
  RequestUnlockButton,
} from "@js/invenio_requests/components/Buttons";
import {
  RequestLinksExtractor,
  InvenioRequestsAPI,
} from "@js/invenio_requests/api/InvenioRequestApi";
import PropTypes from "prop-types";
import { useState } from "react";

export const LockRequest = ({ request, updateRequest, locked }) => {
  const requestLinksExtractor = new RequestLinksExtractor(request);
  const requestsApi = new InvenioRequestsAPI(requestLinksExtractor);

  const [loading, setLoading] = useState(false);

  return (
    <>
      <Divider />
      {locked ? (
        <RequestUnlockButton
          onClick={async () => {
            setLoading(true);
            await requestsApi.unlockRequest();
            updateRequest({ locked: false });
            setLoading(false);
            window.location.reload();
          }}
          className="request-unlock-button"
          loading={loading}
        />
      ) : (
        <RequestLockButton
          onClick={async () => {
            setLoading(true);
            await requestsApi.lockRequest();
            updateRequest({ locked: true });
            setLoading(false);
            window.location.reload();
          }}
          className="request-lock-button"
          loading={loading}
        />
      )}
    </>
  );
};

LockRequest.propTypes = {
  request: PropTypes.object.isRequired,
  updateRequest: PropTypes.func.isRequired,
  locked: PropTypes.bool.isRequired,
};
