import React from 'react';
import Token from './token';
import {Styles} from 'material-ui';

class SymbolToken extends Token {
	static key = null;

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

export class AndToken extends SymbolToken {
	static key = "__AND__";

	repr = "E";

	color = Styles.Colors.cyan600;

	static expr() {
		return "/";
	}
}

export class OrToken extends SymbolToken {
	static key = "__OR__";

	repr = "OU";

	color = Styles.Colors.teal400;

	static expr() {
		return "+";
	}
}

export class NotToken extends SymbolToken {
	static key = "__NOT__";

	repr = "NÃO";

	color = Styles.Colors.red400;

	static expr() {
		return "!";
	}
}

export class LeftParensToken extends SymbolToken {
	static key = "__LPARENS__";

	repr = "(";

	color = Styles.Colors.orange800;

	static expr() {
		return "(";
	}
}

export class RightParensToken extends SymbolToken {
	static key = "__RPARENS__";

	repr = ")";

	color = Styles.Colors.orange800;

	static expr() {
		return ")";
	}
}
