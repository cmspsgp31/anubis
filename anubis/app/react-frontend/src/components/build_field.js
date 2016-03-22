import React from 'react';
import {SelectField, AutoComplete, TextField,
	DatePickerDialog} from 'material-ui';

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
					key={`field_${options.key}`}
					floatingLabelText={field.label}
					filter={AutoComplete.noFilter}
					fullWidth
					dataSource={options.dataSource}
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
};
