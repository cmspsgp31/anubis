/* eslint-disable react/no-set-state */

import React from 'react';
import I from 'immutable';

import {connect} from 'react-redux';

import {TextField} from 'material-ui';

import {
	TokenEditor,
	tokenPropTypes,
	getStateProps,
	getDispatchProps,
} from './token_editor';

import UnitTokenSelector from './unit_token_selector';


@connect(getStateProps, getDispatchProps)
export class TokenField extends React.Component {
	static propTypes = tokenPropTypes;

	constructor(props) {
		super(props);

		this.state = {
			state: I.fromJS({
				"textExpression": "",
			}),
		};
	}

	componentWillMount() {
		this.setStateFromProps();
	}

	componentDidUpdate(previousProps) {
		if (this.arePropsDiff(previousProps, this.props)) {
			this.setStateFromProps();
		}
	}

	arePropsDiff(prev, curr) {
		let compareKeys = ["textExpression", "canSearch"];

		let comparison = key => (curr[key] instanceof I.Collection) ?
			!curr[key].equals(prev[key]) :
			curr[key] != prev[key];

		return compareKeys.some(comparison);
	}

	setStateFromProps() {
		this.immState = s => s.merge(I.fromJS({
			textExpression: this.props.textExpression,
			canSearch: this.props.canSearch,
		}));
	}

	get searchHtml() {
		/*eslint-disable no-unused-vars */
		let model = this.props.defaultModel;
		let expr = this.immState.get('textExpression');
		let page = 1;
		let sorting = this.props.sortingDefaults.get(model);
		/*eslint-enable no-unused-vars */

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

	handleText = ev => {
		this.immState = s => s.set('textExpression', ev.target.value);
	}

	handleSearch = () => {
		if (this.immState.get('textExpression') != "") {
			this.props.goTo(this.searchHtml);
		}
	}

	render() {
		/*eslint-disable react/no-string-refs*/
		let editor = (
			<TokenEditor
				{...this.props}
				ref="input"
				value={this.immState.get('textExpression')}
			/>
		);
		/*eslint-enable react/no-string-refs*/

		return (
			<div style={{
				display: "flex",
				flexFlow: "rows nowrap",
				justifyContent: 'space-around',
			}}
			>
				<div style={{
					width: "70%",
					margin: "0 auto 20px auto",
				}}
				>
					<TextField
						disabled={!this.immState.get('canSearch')}
						floatingLabelText="Digite aqui sua pesquisa"
						multiLine
						onChange={this.handleText}
						onEnterKeyDown={this.handleSearch}
						style={{
							width: "100%",
							height: "",
							minHeight: "72px",
						}}
					>
						{editor}
					</TextField>
				</div>

				<UnitTokenSelector
					onSearch={this.handleSearch}
				/>
			</div>
		);
	}

}
