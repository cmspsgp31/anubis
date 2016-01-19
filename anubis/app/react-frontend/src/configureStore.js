import React from 'react';
import I from 'immutable';
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
	let creator = applyMiddleware(reduxRouterMiddleware)(createStore);

	return creator(reducer, immState);
}
