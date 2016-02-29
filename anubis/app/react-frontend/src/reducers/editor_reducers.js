import I from 'immutable';
import TokenList from 'components/TokenField/token_list';

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

			let position = state.getIn(['searchResults', 'position']);
			let expression = state.getIn(['searchResults', 'expression']);

			let prevToken = (position > 0) ?
				expression.get(position - 1).toJS() :
				null;

			let nextToken = (position < expression.size) ?
				expression.get(position).toJS() :
				null;

			let tokens = TokenList.connectToken(token, prevToken, nextToken);

			state = tokens.reverse().reduce((state, token) =>
				state.updateIn(['searchResults', 'expression'], expr =>
					expr.insert(position, I.fromJS(token))
				), state);

			return state.updateIn(['searchResults', 'position'], p =>
				p + tokens.length);
		},
		'SET_TEXT_EXPRESSION_EDITOR': (state, action) => state.setIn([
			'searchResults',
			'textExpression',
		], action.payload),
	},
};

