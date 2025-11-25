// This file is part of InvenioRequests
// Copyright (C) 2025 CERN.
//
// Invenio Requests is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React from "react";
import { Divider } from "semantic-ui-react";
import { RequestLockButton } from "@js/invenio_requests/components/Buttons";
import {
  RequestLinksExtractor,
  InvenioRequestsAPI,
} from "@js/invenio_requests/api/InvenioRequestApi";
import PropTypes from "prop-types";
import { useState } from "react";
import { i18next } from "@translations/invenio_requests/i18next";

export const LockRequest = ({ request, updateState }) => {
  const requestLinksExtractor = new RequestLinksExtractor(request);
  const requestsApi = new InvenioRequestsAPI(requestLinksExtractor);
  const { is_locked: isLocked } = request;

  const [loading, setLoading] = useState(false);

  return (
    <>
      <Divider />
      {isLocked ? (
        <RequestLockButton
          onClick={async () => {
            setLoading(true);
            await requestsApi.unlockRequest();
            updateState({ locked: false });
            setLoading(false);
            window.location.reload();
          }}
          className="request-lock-button"
          loading={loading}
          content={i18next.t("Unlock conversation")}
          icon="unlock"
        />
      ) : (
        <RequestLockButton
          onClick={async () => {
            setLoading(true);
            await requestsApi.lockRequest();
            updateState({ locked: true });
            setLoading(false);
            window.location.reload();
          }}
          className="request-lock-button"
          loading={loading}
          content={i18next.t("Lock conversation")}
          icon="lock"
        />
      )}
    </>
  );
};

LockRequest.propTypes = {
  request: PropTypes.object.isRequired,
  updateState: PropTypes.func.isRequired,
};
