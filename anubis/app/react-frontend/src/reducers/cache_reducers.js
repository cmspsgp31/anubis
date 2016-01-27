import I from 'immutable';

export let CacheDetails = {
	ReducerMap: {
		'FETCH_DETAILS': (state, action) => {
			if (!action.payload.get) return state;

			let model = action.payload.get("model");
			let id = action.payload.getIn(["object", "id"]);

			if (!I.Map.isMap(state)) state = I.Map();

			return state.updateIn([model, `${id}`], () => action.payload);
		},
	},
	keyPath: ["cache", "details"]
}

export let CacheSearch = {
	ReducerMap: {
		'FETCH_SEARCH': (state, action) => {
			if (!action.payload.get) return state;

			let expr = action.payload.get('textExpression');
			let model = action.payload.get('model');
			let page = action.payload.getIn(['pagination', 'currentPage'], "0");
			let sorting = action.payload.getIn(['sorting', 'current', 'by']);

			if (!sorting) sorting = "none";

			sorting = ((action.payload.getIn(['sorting', 'current',
				'ascending'])) ? "+" : "-") + sorting;

			if (!I.Map.isMap(state)) state = I.Map();

			return state.updateIn([model, expr, sorting, `${page}`],
				() => action.payload);
		},
		'CLEAR_SEARCH_CACHE': (state, action) => {
			let keys = action.payload;

			return state.deleteIn([keys.model, keys.expr, keys.sorting,
					`${keys.page}`]);
		}
	},
	keyPath: ["cache", "searchResults"]
}
