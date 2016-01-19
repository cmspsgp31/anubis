import {createAction} from 'redux-actions';

export default class Actions {
	static increment = createAction('INCREMENT');
	static decrement = createAction('DECREMENT');
}
