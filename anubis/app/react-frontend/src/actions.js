import {createAction} from 'redux-actions';
import I from 'immutable';

export default class Actions {
	static clearDetails = createAction('CLEAR_DETAILS');

	static fetchDetails = createAction('FETCH_DETAILS',
		async link => {
			let response = await fetch(link);
			let json = await response.json();

			return I.fromJS(json.details);
		});

	static restoreDetails = createAction('FETCH_DETAILS')
}
