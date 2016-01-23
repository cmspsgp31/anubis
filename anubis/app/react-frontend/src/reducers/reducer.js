import reduceReducers from 'reduce-reducers';
import {handleActions} from 'redux-actions';

import {Details} from './api_reducers';
import {CacheDetails} from './cache_reducers';

export let appReducers = [Details, CacheDetails];

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

