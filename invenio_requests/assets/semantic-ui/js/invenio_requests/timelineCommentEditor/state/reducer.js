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
  SETTING_CONTENT,
  RESTORE_CONTENT,
  APPEND_CONTENT,
} from "./actions";

const initialState = {
  error: null,
  isLoading: false,
  commentContent: "",
  // commentContent: {comment: "", files: []},
  storedCommentContent: null,
  appendedCommentContent: "",
  // filesList: ,
};

export const commentEditorReducer = (state = initialState, action) => {
  console.log(`commentEditorReducer ${action.type}`);
  switch (action.type) {
    case SETTING_CONTENT:
      // TODO: File list here?
      return { ...state, commentContent: action.payload };
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
        // commentContent: {comment: "", files: []},
      };
    case RESTORE_CONTENT:
      return {
        ...state,
        commentContent: action.payload,
        files: ['todo.txt'],
        // We'll never change this later, so it can be used as an `initialValue`
        storedCommentContent: action.payload,
      };
    default:
      return state;
  }
};
