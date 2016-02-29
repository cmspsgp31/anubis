/* eslint-disable react/no-set-state */

import React from 'react';
import IPropTypes from 'react-immutable-proptypes';
import _ from 'lodash';

import {PropTypes as RPropTypes} from 'react';
import {TransitionMotion, spring} from 'react-motion';

import EditorToken from './editor_token';
import * as SymbolTokens from './symbol_token';
import UnitToken from './unit_token';

export default class TokenList extends React.Component {
	static propTypes = {
		canSearch: RPropTypes.bool,
		createTokenEditor: RPropTypes.func,
		defaultFilter: RPropTypes.string,
		deleteTokenEditor: RPropTypes.func,
		expression: IPropTypes.listOf(
			IPropTypes.contains({
				key: RPropTypes.string.isRequired,
				index: RPropTypes.number.isRequired,
				args: IPropTypes.listOf(RPropTypes.string),
			}),
		),
		fieldsets: IPropTypes.mapOf({
			choices: IPropTypes.list,
			help_text: RPropTypes.string,
			is_numeric: RPropTypes.bool.isRequired,
			label: RPropTypes.string,
			required: RPropTypes.bool.isRequired,
			ui_element: RPropTypes.string.isRequired,
		}),
		focus: RPropTypes.func,
		isFocused: RPropTypes.func,
		modifyInnerFieldEditor: RPropTypes.func,
		moveTokenEditor: RPropTypes.func,
		onBlur: RPropTypes.func.isRequired,
		onChange: RPropTypes.func.isRequired,
		onFocus: RPropTypes.func.isRequired,
		onKeyDown: RPropTypes.func.isRequired,
		onSearch: RPropTypes.func.isRequired,
		position: RPropTypes.number,
		setTextExpressionEditor: RPropTypes.func,
		value: RPropTypes.string,
	};

	constructor(props) {
		super(props);

		this.state = {
			tokens: [],
			editorValue: "",
		};
	}

	componentWillMount() {
		this.getTokens();
	}

	componentDidUpdate(prevProps) {
		if (this.areExprsDiff(prevProps.expression, this.props.expression)) {
			this.getTokens();
		}
	}

	areExprsDiff(prev, current) {
		if (prev.size != current.size) return true;

		return _.zip(prev.toJS(), current.toJS()).some(([p, c]) => {
			if (p.key != c.key) return true;

			if ((!!p.args && !c.args) || (!p.args && !!c.args)) return true;

			if (!p.args) return false;

			if (p.args.length != c.args.length) return true;

			return _.zip(p.args, c.args).some(([pa, ca]) => pa != ca);
		});
	}

	get inputProps() {
		let {onBlur,  onFocus, onKeyDown} = this.props;

		return {onBlur, onChange: this.handleChange, onFocus, onKeyDown};
	}

	handleChange = ev => {
		this.setState({editorValue: ev.target.value});
		return this.props.onChange({target: {value: this.props.value}});
	}

	getTokens() {
		this.tokenObjects = [];

		this.setState({tokens: this.props.expression.map((obj, i) => {
			let key = obj.get('key');
			let fieldset = this.props.fieldsets.get(key);
			let values = obj.get('args', null);
			let id = obj.get('index');

			if (!fieldset) fieldset = {key};
			else fieldset = fieldset.toJS();

			if (values && values.toJS) values = values.toJS();

			let props = {
				...fieldset,
				values,
				searchKey: key,
				index: i,
				id,
				onRemove: this.props.deleteTokenEditor,
				onChange: this.props.modifyInnerFieldEditor,
			};

			let symbolToken = _.values(SymbolTokens)
				.map(symbol => (symbol.key == key) ? symbol : null)
				.filter(symbol => !!symbol);

			if (symbolToken.length == 1) {
				return React.createElement(symbolToken[0], {
					...props,
					key: `token_${id}`,
					ref: t => this.tokenObjects.push(t),
				});
			}
			else return (
				<UnitToken
					{...props}
					key={`token_${id}`}
					ref={t => this.tokenObjects.push(t)}
				/>
			);
		}).toJS()});

		this.props.setTextExpressionEditor(this.expr);
	}

	get expr() {
		const connectorMap = this.constructor.connectorMap;

		let tokenToExpr = obj => {
			if (_.has(connectorMap, obj.key)) {
				return connectorMap[obj.key];
			}

			return UnitToken.expr(obj);
		};

		let expr = this.props.expression.toJS().map(tokenToExpr);

		if (this.state.editorValue != "") {
			let meta = this.props.fieldsets.get(this.props.defaultFilter);
			let editorToken = this.constructor.buildNewToken(
				this.props.defaultFilter, meta);

			editorToken.args[0] = this.state.editorValue;

			let prevToken = (this.props.position > 0) ?
				this.props.expression.get(this.props.position - 1).toJS() :
				null;

			let nextToken = (this.props.position < this.props.expression.size) ?
				this.props.expression.get(this.props.position).toJS() :
				null;

			let tokens = this.constructor.connectToken(editorToken, prevToken,
				nextToken);

			expr.splice(this.props.position, 0, ...tokens.map(tokenToExpr));
		}

		return expr.join("");
	}

	static buildNewToken(key, meta) {
		let token = {
			key,
			index: Date.now(),
		};

		if (meta) {
			token.args = meta.get('fields').map(f => {
				let arg = null;
				if (f.get('ui_element') == "SelectField") {
					arg = f.getIn(['choices', 0, 0]);
				}
				else {
					arg = f.get('initial');
				}

				return `${arg}`;
			}).toJS();
		}

		return token;
	}

	static connectToken(created, prev={}, next={}) {
		prev = Object.assign({}, {key: "__AND__"}, prev);
		next = Object.assign({}, {key: "__AND__"}, next);

		let isCreatedUnitToken = !_.has(this.connectorMap,
			created.key);

		let prevRequiresConnector = !_.has(this.connectorMap,
			prev.key) || (prev.key == "__RPARENS__");

		let nextRequiresConnector = !_.has(this.connectorMap,
			next.key) || (next.key == "__LPARENS__");

		let tokens = [created];

		if (isCreatedUnitToken && prevRequiresConnector) {
			tokens.splice(0, 0, {
				key: "__AND__",
				index: Date.now() + Math.floor(Math.random() * 100 + 10),
			});
		}

		if (isCreatedUnitToken && nextRequiresConnector) {
			tokens.splice(tokens.length, 0, {
				key: "__AND__",
				index: Date.now() + Math.floor(Math.random() * 100 + 20),
			});
		}

		return tokens;
	}

	static connectorMap = {
		"__AND__": "/",
		"__OR__": "+",
		"__NOT__": "!",
		"__LPARENS__": "(",
		"__RPARENS__": ")",
	}

	getInputNode() {
		return {
			blur: () => this.editorToken.lead.blur(),
			focus: () => this.editorToken.lead.focus(),
		};
	}

	get shouldDisable() {
		return false;
	}

	render() {
		let styles = this.state.tokens.map(token => ({
				key: `token_${token.props.id}`,
				data: token,
				style: {
					opacity: spring(1, {precision: 0.1}),
					left: spring(0, {precision: 10}),
				},
		}));

		styles.splice(this.props.position, 0, {
			key: "editor_token",
			style: {},
			data:
				<EditorToken
					deleteToken={this.props.deleteTokenEditor}
					disabled={this.shouldDisable}
					expressionSize={this.props.expression.size}
					inputProps={this.inputProps}
					insertToken={this.props.createTokenEditor}
					isFocused={this.props.isFocused}
					move={this.props.moveTokenEditor}
					onSearch={this.props.onSearch}
					position={this.props.position}
					ref={c => this.editorToken = c}
					units={this.props.fieldsets}
				/>,
		});

		return (
			<TransitionMotion
				styles={styles}
				willEnter={() => ({
					opacity: 0,
					left: -100,
				})}
				willLeave={() => ({
					opacity: spring(0, {precision: 0.1}),
					left: spring(100, {precision: 10}),
				})}
			>
				{styles =>
					<div
						onTouchTap={ev => {
							if (ev.target == this.mainEditingArea) {
								this.props.focus();
							}
						}}
						ref={c => this.mainEditingArea = c}
						style={{
							display: "flex",
							flexFlow: "row wrap",
							justifyContent: "flex-start",
							alignContent: "flex-start",
							paddingTop: "45px",
							paddingBottom: "10px",
						}}
					>
						{styles.map(style =>
							React.cloneElement(style.data, {
								style: style.style,
								key: style.key,
							})
						)}

					</div>
				}
			</TransitionMotion>
		);
	}

}
