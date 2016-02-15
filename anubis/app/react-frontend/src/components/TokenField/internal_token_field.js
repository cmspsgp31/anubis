import React from 'react';
import IPropTypes from 'react-immutable-proptypes';
import {PropTypes as RPropTypes} from 'react';

import {routeActions} from 'redux-simple-router';

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
});

export const getDispatchProps = dispatch => ({
	goTo: url => dispatch(routeActions.push(url)),
});

export class InternalTokenField extends React.Component {
	static propTypes = Object.assign({}, tokenPropTypes, {
		disabled: RPropTypes.bool,
		onBlur: RPropTypes.func,
		onChange: RPropTypes.func,
		onFocus: RPropTypes.func,
		onKeyDown: RPropTypes.func,
		style: RPropTypes.object,
	});

	getInputNode() {
		return this.lead;
	}

	setValue(value) {
		this.lead = value;
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

		return (
			<div
				style={style}
			>
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

