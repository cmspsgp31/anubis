import {createAction} from 'redux-actions';
import I from 'immutable';

let server = prop => async link => {
	let response = await fetch(link, {credentials: 'same-origin'});
	let json = await response.json();

	if (response.status != 200) throw json;

	return I.fromJS(json[prop]);
};

export default class Actions {
	static clearDetails = createAction('CLEAR_DETAILS');

	static fetchDetails = createAction('FETCH_DETAILS', server('details'));

	static restoreDetails = createAction('FETCH_DETAILS');

	static clearSearch = createAction('CLEAR_SEARCH');

	static fetchSearch = createAction('FETCH_SEARCH', server('searchResults'));

	static restoreSearch = createAction('FETCH_SEARCH');

	static clearSearchCache = createAction('CLEAR_SEARCH_CACHE');

	static setGlobalError = createAction('SET_GLOBAL_ERROR');

	static showGlobalErrorDetails = createAction('SHOW_GLOBAL_ERROR_DETAILS');

	static clearGlobalError = createAction('CLEAR_GLOBAL_ERROR');

	static enableEditor = createAction('ENABLE_EDITOR');

	static disableEditor = createAction('DISABLE_EDITOR');

	static toggleEditor = createAction('TOGGLE_EDITOR');
}
