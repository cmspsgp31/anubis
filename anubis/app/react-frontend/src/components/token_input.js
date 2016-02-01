import React from 'react';
import I from 'immutable';

import {connect} from 'react-redux';
import {TextField} from 'material-ui';
import {routeActions} from 'redux-simple-router';

let getStateProps = state => ({
	textExpression: state.getIn(['searchResults', 'textExpression']),
	modelName: state.getIn(['searchResults', 'model']),
	expression: state.getIn(['searchResults', 'expression']),
	searchHtml: state.getIn(['applicationData', 'searchHtml']),
	defaultModel: state.getIn(['applicationData', 'defaultModel']),
	sortingDefaults: state.getIn(['applicationData', 'sortingDefaults']),
	isSearch: state.getIn(['searchResults', 'visible']),
});

let getDispatchProps = dispatch => ({
	goTo: url => dispatch(routeActions.push(url)),
});

@connect(getStateProps, getDispatchProps)
export default class TokenInput extends React.Component {
	constructor(props) {
		super(props);

		this.state = {
			state: I.fromJS({"textExpression": ""})
		};
	}

	get searchHtml() {
		let model = this.props.defaultModel;
		let expr = this.immState.get('textExpression');
		let page = 1;
		let sorting = this.props.sortingDefaults.get(model);

		return eval("`" + this.props.searchHtml + "`");
	}

	set immState(fn) {
		this.setState(({state}) => ({state: fn(state)}));
	}

	get immState() {
		return this.state.state;
	}

	get shouldDisable() {
		return false;
	}

	setExpression(expr) {
		this.immState = s => s.set('textExpression', expr);
	}

	componentWillMount() {
		if (this.props.textExpression != "") {
			this.setExpression(this.props.textExpression);
		}
	}

	componentDidUpdate(previousProps) {
		let textChanged = this.props.textExpression !=
			previousProps.textExpression;

		if (textChanged) {
			this.setExpression(this.props.textExpression);
		}
	}

	handleText = ev => {
		this.setExpression(ev.target.value);
	}

	handleSearch = ev => {
		this.props.goTo(this.searchHtml);
	}

	render() {
		return <div style={{
			display: "flex",
			flexFlow: "rows nowrap",
			justifyContent: 'space-around'
		}}>
			<div style={{
				width: "70%",
				margin: "0 auto 20px auto"
			}}>
				<TextField
					disabled={this.shouldDisable}
					style={{width: "100%"}}
					value={this.immState.get('textExpression')}
					onChange={this.handleText}
					onEnterKeyDown={this.handleSearch}
					/>
			</div>
		</div>;
	}

}
