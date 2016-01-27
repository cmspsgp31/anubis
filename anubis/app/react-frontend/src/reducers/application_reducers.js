import I from 'immutable';

export let App = {
	ReducerMap: {
		'SET_GLOBAL_ERROR': (state, action) => {
			return state
				.set('globalError', action.payload)
				.set('showErrorDetails', false);
		},
		'SHOW_GLOBAL_ERROR_DETAILS': (state, action) => {
			return state.set('showErrorDetails', true);
		},
		'CLEAR_GLOBAL_ERROR': (state, action) => {
			return state.remove('globalError').remove('showErrorDetails');
		}
	},
	keyPath: ['applicationData']
}
