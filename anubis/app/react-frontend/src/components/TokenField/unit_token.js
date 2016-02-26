import React from 'react';
import IPropTypes from 'react-immutable-proptypes';
import {PropTypes as RPropTypes} from 'react';

import _ from 'lodash';


import Token from './token';


export class UnitToken extends Token {
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
		key: RPropTypes.string,
		values: IPropTypes.list,
	});

	get fieldsValues() {
		return _.zip(this.props.fields, this.props.values);
	}

	get expr() {
		let key = this.props.key;
		let values = this.fieldsValues
			.map(([field, value]) => this.formatValue(field, value)
				.replace(/\$/g, "$$")
				.replace(/"/g, '$"'))
			.reduce((agg, value) => agg + `,"${value}"`, "");

		if (this.props.fields.size() == 0) values = ',""';

		return `${key}${values}`;
	}

	formatValue(field, value) {
		return value;
	}

	handleFieldChange = ev => {
		console.log(ev.target.value);
	}

	makeField = hideLabel => {
		return ([field, value], i) => {
			return (
				<div key={i}>
					{!hideLabel &&
						<div
							style={{display: "inline-block"}}
						>
							{field.get('label')}
						</div>
					}
					<input
						onChange={this.handleFieldChange}
						style={{display: "inline-block"}}
						type="text"
						value={value}
					/>
				</div>
			);
		};
	}

	renderContents() {
		let hideLabel = this.props.fields.size() == 1;
		let description = (hideLabel) ?
			this.props.fields.get(1).get("label") :
			this.props.description;


		return (
			<div
				style={{
					display: "flex",
					flexFlow: "row no-wrap",
					height: "20px",
					justifyContent: "flex-start",
				}}
			>
				<p>{description}</p>
				{this.fieldsValues.map(this.makeField(hideLabel)).toJS()}
			</div>
		);

	}
}

