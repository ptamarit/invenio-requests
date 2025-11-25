// This file is part of InvenioRequests
// Copyright (C) 2025 CERN.
//
// Invenio Requests is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React from "react";
import { Divider, Popup, Icon, Grid } from "semantic-ui-react";
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

  const popupContent = isLocked
    ? i18next.t(
        "Unlocking the conversation will allow all users with access to the request to add or update comments."
      )
    : i18next.t(
        "Locking the conversation will only allow the request receivers to add or update comments."
      );
  return (
    <>
      <Divider />
      <Grid columns={2}>
        <Grid.Column floated="left" width={13}>
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
        </Grid.Column>
        <Grid.Column
          floated="right"
          width={3}
          verticalAlign="middle"
          textAlign="center"
        >
          <Popup
            content={popupContent}
            trigger={
              <span role="button" tabIndex="0">
                <Icon name="question circle outline" />
              </span>
            }
          />
        </Grid.Column>
      </Grid>
    </>
  );
};

LockRequest.propTypes = {
  request: PropTypes.object.isRequired,
  updateState: PropTypes.func.isRequired,
};
