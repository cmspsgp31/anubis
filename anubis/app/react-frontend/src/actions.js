import {createAction} from 'redux-actions';

export default class Actions {
	static increment = createAction('increment');
	static decrement = createAction('decrement');
}
