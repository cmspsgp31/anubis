export let Details = {
	ReducerMap: {
		'FETCH_DETAILS': (state, action) => {
			return action.payload;
		},
		'CLEAR_DETAILS': (state, action) => {
			return null;
		}
	},
	keyPath: ["details"]
};
