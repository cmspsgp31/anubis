// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// actions.js - actions definitions for modifying state.

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

import {createAction} from 'redux-actions';
import I from 'immutable';

const server = prop => async link => {
    const response = await fetch(link, {credentials: 'same-origin'});
    const json = await response.json();

    if (response.status != 200) throw json;

    return I.fromJS(json[prop]);
};

export default class Actions {
    static clearDetails = createAction('CLEAR_DETAILS');

    static fetchDetails = createAction('FETCH_DETAILS', server('details'));

    static restoreDetails = createAction('FETCH_DETAILS');

    static clearSearch = createAction('CLEAR_SEARCH');

    static fetchSearch = createAction('FETCH_SEARCH', server('searchResults'));

    static restoreSearch = createAction('FETCH_SEARCH');

    static clearSearchCache = createAction('CLEAR_SEARCH_CACHE');

    static setGlobalError = createAction('SET_GLOBAL_ERROR');

    static showGlobalErrorDetails = createAction('SHOW_GLOBAL_ERROR_DETAILS');

    static clearGlobalError = createAction('CLEAR_GLOBAL_ERROR');

    static startServerAction = createAction('START_ACTION');

    static cancelServerAction = createAction('CANCEL_ACTION');

    static submitServerAction = createAction('FETCH_SEARCH',
        async (url, data) => {
            const response = await fetch(url, {
                credentials: 'same-origin',
                method: 'POST',
                body: data,
                headers: new Headers({
                    'X-CSRFToken': document
                        .querySelector('meta[name="csrf-token"]')
                        .attributes.content.value,
                }),
            });

            const json = await response.json();

            if (response.status != 200) throw json;

            return I.fromJS(json['searchResults']);

        });

    static enableEditor = createAction('ENABLE_EDITOR');

    static disableEditor = createAction('DISABLE_EDITOR');

    static toggleEditor = createAction('TOGGLE_EDITOR');

    static modifyInnerFieldEditor = createAction('MODIFY_INNER_FIELD_EDITOR');

    static moveTokenEditor = createAction('MOVE_TOKEN_EDITOR');

    static createTokenEditor = createAction('CREATE_TOKEN_EDITOR');

    static deleteTokenEditor = createAction('DELETE_TOKEN_EDITOR');

    static setTextExpressionEditor = createAction('SET_TEXT_EXPRESSION_EDITOR');

    static expandDefaultUnitEditor = createAction('EXPAND_DEFAULT_UNIT_EDITOR');

    static buildTextExprEditor = createAction('BUILD_TEXT_EXPR_EDITOR');

    static toggleSearchEditor = createAction('TOGGLE_SEARCH_EDITOR');

    static reorderTokensEditor = createAction('REORDER_TOKENS_EDITOR');
}
