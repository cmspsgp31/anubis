import React from 'react';
import IPropTypes from 'react-immutable-proptypes';
import {PropTypes as RPropTypes} from 'react';

import {routeActions} from 'react-router-redux';

export const tokenPropTypes = {
	canSearch: RPropTypes.bool,
	defaultModel: RPropTypes.string,
	expression: IPropTypes.map,
	goTo: RPropTypes.func,
	isSearch: RPropTypes.bool,
	modelName: RPropTypes.string,
	searchHtml: RPropTypes.string,
	sortingDefaults: IPropTypes.map,
	textExpression: RPropTypes.string,
};

export const getStateProps = state => ({
	textExpression: state.getIn(['searchResults', 'textExpression']),
	modelName: state.getIn(['searchResults', 'model']),
	expression: state.getIn(['searchResults', 'expression']),
	searchHtml: state.getIn(['applicationData', 'searchHtml']),
	defaultModel: state.getIn(['applicationData', 'defaultModel']),
	sortingDefaults: state.getIn(['applicationData', 'sortingDefaults']),
	canSearch: state.getIn(['tokenEditor', 'canSearch']),
	fieldsets: state.getIn(['tokenEditor', 'fieldsets']),
});

export const getDispatchProps = dispatch => ({
	goTo: url => dispatch(routeActions.push(url)),
});

export class TokenEditor extends React.Component {
	static propTypes = Object.assign({}, tokenPropTypes, {
		disabled: RPropTypes.bool,
		onBlur: RPropTypes.func,
		onChange: RPropTypes.func,
		onFocus: RPropTypes.func,
		onKeyDown: RPropTypes.func,
		style: RPropTypes.object,
		value: RPropTypes.string,
		fieldsets: IPropTypes.map,
		expression: IPropTypes.listOf(
			IPropTypes.contains({
				key: RPropTypes.string.isRequired,
				args: IPropTypes.listOf(RPropTypes.string),
			}),
		),
	});

	getInputNode() {
		return this.lead;
	}

	setValue(value) {
		this.lead = value;
	}

	get inputProps() {
		let {disabled, onBlur, onChange, onFocus, onKeyDown} = this.props;

		return {disabled, onBlur, onChange, onFocus, onKeyDown};
	}

	get tokens() {
		return this.props.expression.map(obj => {
			let key = obj.get('key');
			let fieldset = this.props.fieldsets.get(key);
			let values = obj.get('args', null);

			if (!fieldset) fieldset = {key};
			else fieldset = fieldset.toJS();

			if (values && values.toJS) values = values.toJS();

			return {...fieldset, values, key};
		}).toJS();
	}

	render() {
		let style = Object.assign({}, this.props.style, {
			// border: "1px solid black",
		});

		let inputStyle = Object.assign({}, this.props.style, {
			height: "",
			width: "",
			marginTop: "35px",
			border: "1px solid black",
		});

		console.log(this.tokens);

		return (
			<div
				style={style}
			>
				{this.tokens.map(({key}) =>
					<div>
					</div>
				)}

				<input
					disabled={this.props.disabled}
					onBlur={this.props.onBlur}
					onChange={this.props.onChange}
					onFocus={this.props.onFocus}
					onKeyDown={this.props.onKeyDown}
					ref={c => this.lead = c}
					style={inputStyle}
					value={this.props.value}
				/>
			</div>
		);

	}
}

