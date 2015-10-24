import React from 'react';
import {handleActions} from 'redux-actions';
import I from 'immutable';
import {reduxReactRouter, routerStateReducer} from 'redux-router';
import reduceReducers from 'reduce-reducers';
import createHistory from "npm:history@1.12.3/lib/createBrowserHistory";
import promise from 'redux-promise';
import {createStore, applyMiddleware, compose} from 'redux';

function routerGetter(state) {
	return state.get("router");
}

function routerSetter(state, action) {
	return state.update("router", r => routerStateReducer(r, action));
}

export default function (baseReducer, initialState) {
	let immState = I.fromJS(initialState);

	let reducer = reduceReducers(handleActions(baseReducer), routerSetter);

	let creator = compose(
		applyMiddleware(promise),
		reduxReactRouter({ createHistory, routerStateSelector: routerGetter })
	)(createStore);

	return creator(reducer, immState);
}
