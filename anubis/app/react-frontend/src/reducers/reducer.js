import reduceReducers from 'reduce-reducers';
import {handleActions} from 'redux-actions';

import {Details, Search} from 'reducers/api_reducers';
import {CacheDetails, CacheSearch} from 'reducers/cache_reducers';
import {App} from 'reducers/application_reducers';

export let appReducers = [Details, CacheDetails, Search, CacheSearch, App];

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

