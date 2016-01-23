import I from 'immutable';

export let CacheDetails = {
	ReducerMap: {
		'FETCH_DETAILS': (state, action) => {
			let model = action.payload.get("model");
			let id = action.payload.getIn(["object", "id"]);

			if (!I.Map.isMap(state)) state = I.Map();

			return state.updateIn([model, `${id}`], () => action.payload);
		},
	},
	keyPath: ["cache", "details"]
}
