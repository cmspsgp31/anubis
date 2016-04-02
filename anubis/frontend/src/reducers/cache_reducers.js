// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// cache_reducers.js - reducers that deal with the internal search cache.

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

export const CacheDetails = {
    ReducerMap: {
        'FETCH_DETAILS': (state, action) => {
            if (!action.payload.get) return state;

            const model = action.payload.get("model");
            const id = action.payload.getIn(["object", "id"]);

            if (!I.Map.isMap(state)) state = I.Map();

            return state.updateIn([model, `${id}`], () => action.payload);
        },
    },
    keyPath: ["cache", "details"],
};

export const CacheSearch = {
    ReducerMap: {
        'FETCH_SEARCH': (state, action) => {
            if (!action.payload.get) return state;

            const expr = action.payload.get('textExpression');
            const model = action.payload.get('model');
            const page = action.payload.getIn(['pagination', 'currentPage'],
                                              "0");
            let sorting = action.payload.getIn(['sorting', 'current', 'by']);

            if (!sorting) sorting = "none";

            sorting = ((action.payload.getIn(['sorting', 'current',
                                             'ascending'])) ? "+" : "-"
                      ) + sorting;

            if (!I.Map.isMap(state)) state = I.Map();

            return state.updateIn([model, expr, sorting, `${page}`],
                () => action.payload);
        },
        'CLEAR_SEARCH_CACHE': (state, action) => {
            const keys = action.payload;

            return state.deleteIn([keys.model, keys.expr, keys.sorting,
                    `${keys.page}`]);
        },
    },
    keyPath: ["cache", "searchResults"],
};
