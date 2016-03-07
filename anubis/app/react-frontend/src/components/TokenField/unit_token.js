import React from 'react';
import IPropTypes from 'react-immutable-proptypes';
import Intl from 'intl';

import {PropTypes as RPropTypes} from 'react';
import {TextField, SelectField, MenuItem, DatePickerDialog} from 'material-ui';
import {ActionDateRange} from 'material-ui/lib/svg-icons';

import _ from 'lodash';

import Token, {makeDraggable} from './token';

@makeDraggable
export default class UnitToken extends Token {
	static propTypes = Object.assign({}, Token.propTypes, {
		description: RPropTypes.string,
		fields: IPropTypes.listOf(
			IPropTypes.contains({
				choices: IPropTypes.listOf(
					IPropTypes.contains({2: RPropTypes.any.isRequired}),
				),
				help_text: RPropTypes.string,
				is_numeric: RPropTypes.bool,
				label: RPropTypes.string,
				required: RPropTypes.bool,
				ui_element: RPropTypes.string,
			}),
		),
		index: RPropTypes.number,
		onChange: RPropTypes.func,
		onSearch: RPropTypes.func,
		searchKey: RPropTypes.string,
		values: IPropTypes.list,
	});

	get fieldsValues() {
		return _.zip(this.props.fields, this.props.values);
	}

	handleFieldChange = index => {
		return (ev, _, value) => {
			value = (ev.target.value == null) ? value : ev.target.value;

			let payload = {
				tokenIndex: this.props.index,
				fieldIndex: index,
				value,
			};

			this.props.onChange(payload);
		};
	}

	makeField = hideLabel => {
		return ([field, value], i) => {
			let input = null;

			let insideStyle = {
				color: this.style.color,
				top: "-10px",
				height: "auto",
				lineHeight: "normal",
				userSelect: "all",
			};

			let outsideStyle = {
				display: "inline-block",
				fontSize: 14,
				margin: 0,
				height: "auto",
				top: "10px",
			};

			switch (field.ui_element) {
				case "SelectField":
					input = (
						<SelectField
							autoWidth
							iconStyle={{top: -14}}
							labelStyle={insideStyle}
							onChange={this.handleFieldChange(i)}
							style={outsideStyle}
							value={`${value}`}
						>
							{field.choices.map(([choice, text]) => (
								<MenuItem
									key={`${choice}`}
									primaryText={text}
									value={`${choice}`}
								/>
							))}
						</SelectField>
					);
					break;

				case "DatePicker":
					input = (
						<div
							style={{display: "inline-block"}}
						>
							<TextField
								hintText={field.help_text}
								inputStyle={insideStyle}
								onChange={this.handleFieldChange(i)}
								onEnterKeyDown={this.props.onSearch}
								style={{...outsideStyle, width: "205px"}}
								value={value}
							/>
							{this.makeIconButton(ActionDateRange, {
								iconStyle: {
									width: 24,
									height: 24,
								},
								props: {
									onClick: () => {
										this.datePickers[i].show();
									},
								},
							})}
							<DatePickerDialog
								DateTimeFormat={Intl.DateTimeFormat}
								autoOk
								firstDayOfWeek={0}
								locale="pt-BR"
								maxDate={new Date()}
								onAccept={date => {
									date = new Intl.DateTimeFormat("pt-BR")
										.format(date);

									this.handleFieldChange(i)({
										target: {value: date},
									}, null, date);
								}}
								ref={c => this.datePickers[i] = c}
							/>
						</div>
					);
					break;

				default:
					input = (
						<TextField
							hintText={field.help_text}
							inputStyle={insideStyle}
							onChange={this.handleFieldChange(i)}
							onEnterKeyDown={this.props.onSearch}
							style={{...outsideStyle, width: "auto"}}
							value={value}
						/>
					);
			}

			return (
				<div key={i}>
					{!hideLabel &&
						<div
							style={{
								display: "inline-block",
								margin: "0 6px",
							}}
						>
							{field.label}
						</div>
					}
					{input}
				</div>
			);
		};
	}

	renderContents() {
		let hideLabel = this.props.fields.length == 1;
		let description = (hideLabel) ?
			this.props.fields[0].label :
			this.props.description;

		this.datePickers = {};

		return (
			<div
				style={{
					display: "inline-flex",
					flexFlow: "row no-wrap",
					justifyContent: "flex-start",
				}}
			>
				<p
					style={{
						marginRight: "12px",
						...this.uppercaseStyle,
					}}
				>
					{description}
				</p>
				{this.fieldsValues.filter(([f]) => f)
					.map(this.makeField(hideLabel))}
			</div>
		);

	}
}

