// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// build_field.js - a function for building fields.

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
import {AutoComplete} from 'material-ui';

export default function (field, options={}) {
    field = field.toJS();

    options = Object.assign({}, {
        dataSource: [],
        key: null,
        onSelect: () => null,
        onUpdateInput: () => null,
        onClearInput: () => null,
        timer: null,
    }, options);

    let input = null;

    switch (field.ui_element) {
        case "AutoComplete":
            input = (
                <AutoComplete
                    dataSource={options.dataSource}
                    filter={AutoComplete.noFilter}
                    floatingLabelText={field.label}
                    fullWidth
                    key={`field_${options.key}`}
                    onNewRequest={options.onSelect}
                    onUpdateInput={searchText => {
                        if (options.timer) {
                            clearTimeout(options.timer);
                            options.timer = null;
                        }

                        options.timer = setTimeout(() => {
                            if (searchText.length >= 3) {
                                options.onUpdateInput(searchText);
                            }
                            else {
                                options.onClearInput();
                            }
                        }, 200);
                    }}
                />
            );
            break;

        default:
            break;
    }


    return input;
}
