import React from 'react';
import Token from './token';

class SymbolToken extends Token {
	static key = null;

	repr = null;

	get keyCodes() {
		return [];
	}

	renderContents() {
		return <p>{this.repr}</p>;
	}
}

export class AndToken extends SymbolToken {
	static key = "__AND__";

	repr = "E";

	get expr() {
		return "/";
	}
}

export class OrToken extends SymbolToken {
	static key = "__OR__";

	repr = "OU";

	get expr() {
		return "+";
	}
}

export class NotToken extends SymbolToken {
	static key = "__NOT__";

	repr = "NÃO";

	get expr() {
		return "!";
	}
}

export class LeftParensToken extends SymbolToken {
	static key = "__LPARENS__";

	repr = "(";

	get expr() {
		return "(";
	}
}

export class RightParensToken extends SymbolToken {
	static key = "__RPARENS__";

	repr = ")";

	get expr() {
		return ")";
	}
}
