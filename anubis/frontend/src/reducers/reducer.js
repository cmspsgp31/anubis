// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// reducer.js - a function for combining all the application reducers and
//              any others that might be necessary.

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



import reduceReducers from 'reduce-reducers';
import {handleActions} from 'redux-actions';

import {Details, Search} from 'reducers/api_reducers';
import {CacheDetails, CacheSearch} from 'reducers/cache_reducers';
import {App} from 'reducers/application_reducers';
import {Editor} from 'reducers/editor_reducers';

export const appReducers = [
    Details,
    CacheDetails,
    Search,
    CacheSearch,
    App,
    Editor,
];

export const combineReducers = (reducerMapList) => {
    const reducers = reducerMapList.map(({ReducerMap, ...data}) => {
        const reducer = handleActions(ReducerMap);

        if (Object.prototype.hasOwnProperty.call(data, 'keyPath')) {
            const keyPath = data.keyPath;

            return (state, action) => {
                return state.updateIn(keyPath, value => reducer(value, action));
            };
        }
        else return reducer;
    });

    return reduceReducers(...reducers);
};

