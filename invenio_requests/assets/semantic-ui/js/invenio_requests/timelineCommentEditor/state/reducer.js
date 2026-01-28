// This file is part of InvenioRequests
// Copyright (C) 2022-2025 CERN.
// Copyright (C) 2024 KTH Royal Institute of Technology.
//
// Invenio RDM Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import {
  IS_LOADING,
  HAS_ERROR,
  SUCCESS,
  PARENT_RESTORE_DRAFT_CONTENT,
  PARENT_SET_DRAFT_CONTENT,
  PARENT_RESTORE_DRAFT_FILES,
  PARENT_SET_DRAFT_FILES,
  SETTING_FILES,
  RESTORE_FILES,
} from "./actions";

const initialState = {
  error: null,
  isLoading: false,
  commentContent: "",
  files: [],
  storedCommentContent: null,
};

export const commentEditorReducer = (state = initialState, action) => {
  switch (action.type) {
    case PARENT_SET_DRAFT_CONTENT:
      return { ...state, commentContent: action.payload.content };
    case PARENT_SET_DRAFT_FILES:
      return { ...state, files: action.payload.files };
    case SETTING_FILES:
      return { ...state, files: action.payload };
    case IS_LOADING:
      return { ...state, isLoading: true };
    case HAS_ERROR:
      return { ...state, error: action.payload, isLoading: false };
    case SUCCESS:
      return {
        ...state,
        isLoading: false,
        error: null,
        commentContent: "",
        files: [],
      };
    case PARENT_RESTORE_DRAFT_CONTENT:
      return {
        ...state,
        commentContent: action.payload.content,
        // We'll never change this later, so it can be used as an `initialValue`
        storedCommentContent: action.payload.content,
      };
    case PARENT_RESTORE_DRAFT_FILES:
      return {
        ...state,
        files: action.payload.files,
      };
    case RESTORE_FILES:
      return {
        ...state,
        files: action.payload,
      };
    default:
      return state;
  }
};
