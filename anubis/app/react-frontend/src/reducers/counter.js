export class ReducerMap {
	static ['INCREMENT'](state, action) {
		// return state.update('counter', x => x + action.payload);
		return state + action.payload;
	}

	static ['DECREMENT'](state, action) {
		// return state.update('counter', x => x - action.payload);
		return state - action.payload;
	}
};

export let keyPath = ['counter'];
