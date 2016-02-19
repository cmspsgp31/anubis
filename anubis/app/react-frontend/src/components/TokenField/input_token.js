import {PropTypes as RPropTypes} from 'react';

import Token from './token';

export default class InputToken extends Token {
	static propTypes = Object.assign({}, Token.propTypes, {
		onBlur: RPropTypes.func,
		onChange: RPropTypes.func,
		onFocus: RPropTypes.func,
		onKeyDown: RPropTypes.func,
		value: RPropTypes.string,
	})
}

