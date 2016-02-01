import I from 'immutable';

export let Details = {
	ReducerMap: {
		'FETCH_DETAILS': (state, action) => {
			if (action.error) {
				return (state) ? state.set("error", I.fromJS(action.payload)) :
					I.fromJS({error: action.payload});
			}

			return action.payload;
		},
		'CLEAR_DETAILS': (state, action) => null
	},
	keyPath: ["details"]
};

export let Search = {
	ReducerMap: {
		'FETCH_SEARCH': (state, action) => {
			if (action.error) {
				return state.set("error", I.fromJS(action.payload));
			}

			return action.payload;
		},
		'CLEAR_SEARCH': (state, action) => (I.fromJS({
			expression: null,
			textExpression: "",
			pagination: null,
			actions: {},
			visible: false,
			model: state.get('model'),
			results: [],
			sorting: { by: null, ascending: true },
			selection: []
		}))
	},
	keyPath: ["searchResults"]
};
