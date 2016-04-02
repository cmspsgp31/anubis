// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// configureStore.js - basic configuration for the router store.

// This file is part of Anubis.

// Anubis is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// Anubis is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with this program. If not, see <http://www.gnu.org/licenses/>.

import I from 'immutable';
import promiseMiddleware from 'redux-promise';
import reduceReducers from 'reduce-reducers';

import {browserHistory} from 'react-router';
import {syncHistory, routeReducer} from 'react-router-redux';
import {createStore, applyMiddleware} from 'redux';

import {combineReducers} from 'reducers/reducer';

export default function (reducers, initialState) {
    const immState = I.fromJS(initialState);
    const reduxRouterMiddleware = syncHistory(browserHistory);
    const customRouteReducer = (state, action) => {
        return state.update("routing", value => routeReducer(value, action));
    };

    const reducer = reduceReducers(combineReducers(reducers),
                                   customRouteReducer);

    const creator = applyMiddleware(
        reduxRouterMiddleware,
        promiseMiddleware
    )(createStore);

    const store = creator(reducer, immState);

    store.listenForReplays = () => {
        const selectState = state => state.get('routing');

        reduxRouterMiddleware.listenForReplays(store, selectState);
    };

    return store;
}
