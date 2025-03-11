// This file is part of Invenio
// Copyright (C) 2023 CERN.
//
// Invenio is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import {
  SearchAppFacets,
  SearchAppResultsPane,
} from "@js/invenio_search_ui/components";
import { i18next } from "@translations/invenio_requests/i18next";
import { RequestStatusFilter } from "./RequestStatusFilterComponent";
import PropTypes from "prop-types";
import React from "react";
import { GridResponsiveSidebarColumn } from "react-invenio-forms";
import { SearchBar } from "react-searchkit";
import { Button, Container, Grid } from "semantic-ui-react";

import { SharedOrMineFilter } from "@js/invenio_requests/components/SharedOrMineFilter";

export const RequestsSearchLayout = ({ config, appName }) => {
  const [sidebarVisible, setSidebarVisible] = React.useState(false);
  return (
    <Container>
      <Grid>
        <Grid.Row>
          <Grid.Column only="computer" computer={4} />
          <Grid.Column only="mobile tablet" mobile={2} tablet={1}>
            <Button
              basic
              size="medium"
              icon="sliders"
              onClick={() => setSidebarVisible(true)}
              aria-label={i18next.t("Filter results")}
              className="rel-mb-1"
            />
          </Grid.Column>

          <Grid.Column
            mobile={14}
            tablet={7}
            computer={4}
            floated="right"
            className="text-align-right-mobile"
          >
            <SharedOrMineFilter />
          </Grid.Column>

          <Grid.Column
            mobile={16}
            tablet={4}
            computer={3}
            floated="right"
            className="text-align-right-mobile"
          >
            <RequestStatusFilter className="rel-mb-1" keepFiltersOnUpdate />
          </Grid.Column>

          <Grid.Column mobile={16} tablet={16} computer={5}>
            <SearchBar placeholder={i18next.t("Search in my requests...")} />
          </Grid.Column>
        </Grid.Row>

        <Grid.Row>
          <GridResponsiveSidebarColumn
            width={4}
            open={sidebarVisible}
            onHideClick={() => setSidebarVisible(false)}
          >
            <SearchAppFacets aggs={config.aggs} appName={appName} />
          </GridResponsiveSidebarColumn>
          <Grid.Column mobile={16} tablet={16} computer={12}>
            <SearchAppResultsPane
              layoutOptions={config.layoutOptions}
              appName={appName}
            />
          </Grid.Column>
        </Grid.Row>
      </Grid>
    </Container>
  );
};

RequestsSearchLayout.propTypes = {
  config: PropTypes.object.isRequired,
  appName: PropTypes.string,
};

RequestsSearchLayout.defaultProps = {
  appName: undefined,
};
