export class ReducerMap {
	static ['INCREMENT'](state, action) {
		return state + action.payload;
	}

	static ['DECREMENT'](state, action) {
		return state - action.payload;
	}
};

export let keyPath = ['counter'];
