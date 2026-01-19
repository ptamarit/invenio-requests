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
  SETTING_FILES, // TODO: Remove.
  RESTORE_FILES, // TODO: Remove.
} from "./actions";

const initialState = {
  error: null,
  isLoading: false,
  commentContent: "",
  files: [],
  storedCommentContent: null,
  // TODO: appendedCommentContent not here anymore? Indeed.
  // appendedCommentContent: "",
};

export const commentEditorReducer = (state = initialState, action) => {
  switch (action.type) {
    case PARENT_SET_DRAFT_CONTENT:
      console.log("PARENT_SET_DRAFT_CONTENT"); // TODO: Remove.
      return { ...state, commentContent: action.payload.content };
    case PARENT_SET_DRAFT_FILES:
      console.log("PARENT_SET_DRAFT_FILES"); // TODO: Remove.
      return { ...state, files: action.payload.files };
    case SETTING_FILES: // TODO: Remove.
      // TODO: Needed? Used?
      console.error("SETTING_FILES dead code");
      throw new Error("SETTING_FILES dead code")
      // return { ...state, files: action.payload };
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
      console.log("PARENT_RESTORE_DRAFT_CONTENT"); // TODO: Remove.
      return {
        ...state,
        commentContent: action.payload.content,
        // We'll never change this later, so it can be used as an `initialValue`
        storedCommentContent: action.payload.content,
      };
    case PARENT_RESTORE_DRAFT_FILES:
      console.log("PARENT_RESTORE_DRAFT_FILES"); // TODO: Remove.
      return {
        ...state,
        files: action.payload.files,
        // TODO: Or this?
        // files: action.payload,
      };
    case RESTORE_FILES: // TODO: Remove.
      console.error("RESTORE_FILES dead code");
      throw new Error("RESTORE_FILES dead code")
      // TODO: Needed? Used?
      // return {
      //   ...state,
      //   files: action.payload,
      // };
    default:
      return state;
  }
};
