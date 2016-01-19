import * as Counter from './counter.js';
import reduceReducers from 'reduce-reducers';
import {handleActions} from 'redux-actions';

export let appReducers = [ Counter ];

export function combineReducers(reducerMapList) {
	let reducers = reducerMapList.map(({ReducerMap, ...data}) => {
		let reducer = handleActions(ReducerMap);

		if (Object.prototype.hasOwnProperty.call(data, 'keyPath')) {
			let keyPath = data.keyPath;

			return (state, action) => {
				return state.updateIn(keyPath, value => reducer(value, action));
			};
		}
		else return reducer;
	});

	return reduceReducers(...reducers);
}

