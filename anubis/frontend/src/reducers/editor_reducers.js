// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// editor_reducers.js - reducers that deal with the token editor.

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



import TokenList from 'components/TokenField/token_list';
import _ from 'lodash';
import I from 'immutable';

const getNextID = state => {
    const currentID = state.getIn(['tokenEditor', 'counter']);

    return [currentID, state.setIn(['tokenEditor', 'counter'], currentID + 1)];
};

const createAction = (state, token) => {
    const position = state.getIn(['searchResults', 'position']);
    const expression = state.getIn(['searchResults', 'expression']);

    const prevToken = (position > 0) ?
        expression.get(position - 1) :
        null;

    const nextToken = (position < expression.size) ?
        expression.get(position) :
        null;

    const tokens = TokenList.connectToken(token, prevToken, nextToken);

    state = tokens.reverse().reduce((state, token) => {
        const [id, newState] = getNextID(state);

        token = token.set('index', id);

        return newState.updateIn(['searchResults', 'expression'], expr => (
            expr.insert(position, token)
        ));
    }, state);

    return state.updateIn(['searchResults', 'position'], p =>
        p + tokens.length);
};

const unitExpr = obj => {
    const key = obj.get('key');
    let values = obj.get('args')
        .map(value => value.replace(/\$/g, "$$").replace(/"/g, '$"'))
        .reduce((agg, value) => agg + `,"${value}"`, "");

    if (obj.get('args').size == 0) values = ',""';

    return `${key}${values}`;
};

export const Editor = {
    ReducerMap: {
        'ENABLE_EDITOR': state =>
            state.setIn(['tokenEditor', 'canSearch'], true),
        'DISABLE_EDITOR': state =>
            state.setIn(['tokenEditor', 'canSearch'], false),
        'TOGGLE_EDITOR': state =>
            state.updateIn(['tokenEditor', 'canSearch'], v => !v),
        'MODIFY_INNER_FIELD_EDITOR': (state, action) => state.setIn([
            'searchResults',
            'expression',
            action.payload.tokenIndex,
            'args',
            action.payload.fieldIndex,
        ], action.payload.value),
        'DELETE_TOKEN_EDITOR': (state, action) => {
            const position = state.getIn(['searchResults', 'position']);
            const diff = (position > action.payload) ? 1 : 0;

            return state
                .removeIn(['searchResults', 'expression', action.payload])
                .updateIn(['searchResults', 'position'], p => p - diff);
        },
        'MOVE_TOKEN_EDITOR': (state, action) => state.setIn([
            'searchResults', 'position'], action.payload),
        'CREATE_TOKEN_EDITOR': (state, action) => {
            const key = action.payload;
            const meta = state.getIn(['tokenEditor', 'fieldsets', key]);
            const token = TokenList.buildNewToken(key, meta);

            return createAction(state, token);
        },
        'CREATE_TOKEN_EDITOR_WITH_INITIAL': (state, action) => {
            const key = action.payload.key;
            const meta = state.getIn(['tokenEditor', 'fieldsets', key]);
            const args = I.List(action.payload.args).map(value => `${value}`);
            const token = TokenList.buildNewToken(key, meta)
                .set('args', args);

            return createAction(state, token);
        },
        'SET_TEXT_EXPRESSION_EDITOR': (state, action) => state.setIn([
            'searchResults',
            'textExpression',
        ], action.payload),
        'EXPAND_DEFAULT_UNIT_EDITOR': (state, action) => {
            const key = state.getIn(['applicationData', 'defaultFilter']);
            const meta = state.getIn(['tokenEditor', 'fieldsets', key]);
            let token = TokenList.buildNewToken(key, meta);

            token = token.setIn(['args', 0], action.payload);

            return createAction(state, token);
        },
        'BUILD_TEXT_EXPR_EDITOR': state => {
            const connectorMap = TokenList.connectorMap;
            const expression = state.getIn(['searchResults',  'expression']);

            const textExpression = expression.map(obj => {
                if (_.has(connectorMap, obj.get('key'))) {
                    return connectorMap[obj.get('key')];
                }

                return unitExpr(obj);
            }).join("");

            return state.setIn(['searchResults', 'textExpression'],
                textExpression);
        },
        'TOGGLE_SEARCH_EDITOR': state => state.updateIn(['tokenEditor',
            'shouldSearch'], b => !b),
        'REORDER_TOKENS_EDITOR': (state, action) => {
            const expr = state.getIn(['searchResults', 'expression']);
            const tokenMap = I.Map(expr
                .map(t => [`${t.get('index')}`, t])
                .toArray());

            const order = action.payload;
            const position = order.indexOf('__EDITOR__');

            order.splice(position, 1);

            return state
                .setIn(['searchResults', 'expression'],
                    I.List(order.map(id => tokenMap.get(`${id}`))))
                .setIn(['searchResults', 'position'], position);
        },
    },
};

