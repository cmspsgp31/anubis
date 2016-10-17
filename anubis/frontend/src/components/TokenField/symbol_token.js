// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// symbol_token.js - tokens representing connecting symbols.

// This file is part of Anubis.

// Anubis is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// Anubis is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with this program. If not, see <http://www.gnu.org/licenses/>.


import React from 'react';

import * as Colors from 'material-ui/styles/colors';

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

    color = Colors.cyan600;
}

@makeDraggable
class OrToken extends SymbolToken {
    repr = "OU";

    color = Colors.teal400;
}

@makeDraggable
class NotToken extends SymbolToken {
    repr = "NÃO";

    color = Colors.red400;
}

@makeDraggable
class LeftParensToken extends SymbolToken {
    repr = "(";

    color = Colors.orange800;
}

@makeDraggable
class RightParensToken extends SymbolToken {
    repr = ")";

    color = Colors.orange800;
}

export default {
    "__AND__": AndToken,
    "__OR__": OrToken,
    "__NOT__": NotToken,
    "__LPARENS__": LeftParensToken,
    "__RPARENS__": RightParensToken,
};
