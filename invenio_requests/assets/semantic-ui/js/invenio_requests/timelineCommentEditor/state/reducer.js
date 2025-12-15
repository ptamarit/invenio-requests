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
  SETTING_CONTENT,
  RESTORE_CONTENT,
  APPEND_CONTENT,
  SETTING_FILES,
  RESTORE_FILES,
} from "./actions";

const initialState = {
  error: null,
  isLoading: false,
  commentContent: "",
  files: [],
  // commentContent: {comment: "", files: []},
  storedCommentContent: null,
  // TODO: appendedCommentContent not here anymore?
  appendedCommentContent: "",
  // filesList: ,
};

export const commentEditorReducer = (state = initialState, action) => {
  switch (action.type) {
    case PARENT_SET_DRAFT_CONTENT:
      return { ...state, commentContent: action.payload.content };
    case SETTING_CONTENT:
      return { ...state, commentContent: action.payload };
    case SETTING_FILES:
      return { ...state, files: action.payload };
    case APPEND_CONTENT:
      return {
        ...state,
        commentContent: state.commentContent + action.payload,
        // We keep track of appended content separately to trigger the focus event only when
        // text is appended (not when the user is typing).
        appendedCommentContent: state.appendedCommentContent + action.payload,
      };
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
    case RESTORE_FILES:
      return {
        ...state,
        files: action.payload,
      };
    default:
      return state;
  }
};
