import I from 'immutable';
import promiseMiddleware from 'redux-promise';
import reduceReducers from 'reduce-reducers';

import {browserHistory} from 'react-router';
import {syncHistory, routeReducer} from 'react-router-redux';
import {createStore, applyMiddleware} from 'redux';

import {combineReducers} from 'reducers/reducer';

export default function (reducers, initialState) {
	let immState = I.fromJS(initialState);
	let reduxRouterMiddleware = syncHistory(browserHistory);
	let customRouteReducer = (state, action) => {
		return state.update("routing", value => routeReducer(value, action));
	};

	let reducer = reduceReducers(combineReducers(reducers), customRouteReducer);
	let creator = applyMiddleware(
		reduxRouterMiddleware,
		promiseMiddleware
	)(createStore);

	let store = creator(reducer, immState);

	store.listenForReplays = () => {
		let selectState = state => state.get('routing');

		reduxRouterMiddleware.listenForReplays(store, selectState);
	};

	return store;
}
