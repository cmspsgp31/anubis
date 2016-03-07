import React from 'react';

import {Styles} from 'material-ui';

import Token, {makeDraggable} from './token';

class SymbolToken extends Token {
	repr = null;

	color = null;

	get keyCodes() {
		return [];
	}

	get baseStyle() {
		return Object.assign({}, super.baseStyle, this.uppercaseStyle, {
			backgroundColor: this.color,
		});
	}

	renderContents() {
		return <p style={{display: "inline-block"}}>{this.repr}</p>;
	}
}

@makeDraggable
class AndToken extends SymbolToken {
	repr = "E";

	color = Styles.Colors.cyan600;
}

@makeDraggable
class OrToken extends SymbolToken {
	repr = "OU";

	color = Styles.Colors.teal400;
}

@makeDraggable
class NotToken extends SymbolToken {
	repr = "NÃO";

	color = Styles.Colors.red400;
}

@makeDraggable
class LeftParensToken extends SymbolToken {
	repr = "(";

	color = Styles.Colors.orange800;
}

@makeDraggable
class RightParensToken extends SymbolToken {
	repr = ")";

	color = Styles.Colors.orange800;
}

export default {
	"__AND__": AndToken,
	"__OR__": OrToken,
	"__NOT__": NotToken,
	"__LPARENS__": LeftParensToken,
	"__RPARENS__": RightParensToken,
};
