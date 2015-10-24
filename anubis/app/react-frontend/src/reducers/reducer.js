export default class Reducer {
	static increment(state, action) {
		return state.update('counter', x => x + action.payload);
	}

	static decrement(state, action) {
		return state.update('counter', x => x - action.payload);
	}
};
