import TokenList from 'components/TokenField/token_list';
import UnitToken from 'components/TokenField/unit_token';
import _ from 'lodash';

const createAction = (state, token) => {
	let position = state.getIn(['searchResults', 'position']);
	let expression = state.getIn(['searchResults', 'expression']);

	let prevToken = (position > 0) ?
		expression.get(position - 1) :
		null;

	let nextToken = (position < expression.size) ?
		expression.get(position) :
		null;

	let tokens = TokenList.connectToken(token, prevToken, nextToken);

	state = tokens.reverse().reduce((state, token) =>
		state.updateIn(['searchResults', 'expression'], expr =>
			expr.insert(position, token)
		), state);

	return state.updateIn(['searchResults', 'position'], p =>
		p + tokens.length);
};

export let Editor = {
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
			let position = state.getIn(['searchResults', 'position']);
			let diff = (position > action.payload) ? 1 : 0;

			return state
				.removeIn(['searchResults', 'expression', action.payload])
				.updateIn(['searchResults', 'position'], p => p - diff);
		},
		'MOVE_TOKEN_EDITOR': (state, action) => state.setIn([
			'searchResults', 'position'], action.payload),
		'CREATE_TOKEN_EDITOR': (state, action) => {
			let key = action.payload;
			let meta = state.getIn(['tokenEditor', 'fieldsets', key]);

			let token = TokenList.buildNewToken(key, meta);

			return createAction(state, token);
		},
		'SET_TEXT_EXPRESSION_EDITOR': (state, action) => state.setIn([
			'searchResults',
			'textExpression',
		], action.payload),
		'EXPAND_DEFAULT_UNIT_EDITOR': (state, action) => {
			let key = state.getIn(['applicationData', 'defaultFilter']);
			let meta = state.getIn(['tokenEditor', 'fieldsets', key]);
			let token = TokenList.buildNewToken(key, meta);

			token = token.setIn(['args', 0], action.payload);

			return createAction(state, token);
		},
		'BUILD_TEXT_EXPR_EDITOR': state => {
			const connectorMap = TokenList.connectorMap;
			let expression = state.getIn(['searchResults',  'expression']);

			let textExpression = expression.map(obj => {
				if (_.has(connectorMap, obj.get('key'))) {
					return connectorMap[obj.get('key')];
				}

				return UnitToken.expr(obj);
			}).join("");

			return state.setIn(['searchResults', 'textExpression'],
				textExpression);
		},
		'TOGGLE_SEARCH_EDITOR': state => state.updateIn(['tokenEditor',
			'shouldSearch'], b => !b),
	},
};

