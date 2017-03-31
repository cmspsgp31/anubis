// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// api_reducers.js - reducers that deal with the search API.

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

export const Details = {
    ReducerMap: {
        'FETCH_DETAILS': (state, action) => {
            if (action.error) {
                return (state) ? state.set("error", I.fromJS(action.payload)) :
                    I.fromJS({error: action.payload});
            }

            return action.payload;
        },
        'CLEAR_DETAILS': () => null,
    },
    keyPath: ["details"],
};

export const Search = {
    ReducerMap: {
        'FETCH_SEARCH': (state, action) => {
            if (action.error) {
                return state.set("error", I.fromJS(action.payload));
            }

            return action.payload;
        },
        'CLEAR_SEARCH': state => (I.fromJS({
            expression: [],
            textExpression: "",
            position: 0,
            pagination: null,
            actions: {},
            visible: false,
            model: state.get('model'),
            results: [],
            sorting: { by: null, ascending: true },
            selection: [],
        })),
        'CANCEL_ACTION': state => state.remove('actionResult'),
        'TOGGLE_SELECTION_SEARCH': (state, {payload: {ids}}) => state
            .update('selection', s => ids.reduce((sel, id) => (sel.has(id) ?
                sel.delete(id) : sel.add(id)), s.toSet()).toList()),
    },
    keyPath: ["searchResults"],
};
