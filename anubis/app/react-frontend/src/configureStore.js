import React from 'react';
import I from 'immutable';
import promiseMiddleware from 'redux-promise';

import {browserHistory} from 'react-router';
import {syncHistory, routeReducer} from 'redux-simple-router';
import {createStore, applyMiddleware, compose} from 'redux';
import {combineReducers} from './reducers/reducer.js';

export default function (reducers, initialState) {
	let immState = I.fromJS(initialState);
	let reduxRouterMiddleware = syncHistory(browserHistory);
	let customRouteReducer = {
		keyPath: ['routing'],
		ReducerMap: routeReducer
	};

	let reducer = combineReducers(reducers.concat(customRouteReducer));
	let creator = applyMiddleware(
		reduxRouterMiddleware,
		promiseMiddleware
	)(createStore);

	let store = creator(reducer, immState);

	store.listenForReplays = () => {
		let selectState = state => state.get('routing');

		reduxRouterMiddleware.listenForReplays(store, selectState);
	}

	return store;
}
