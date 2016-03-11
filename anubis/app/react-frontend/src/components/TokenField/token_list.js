/* eslint-disable react/no-set-state */

import React from 'react';
// import ReactDOM from 'react-dom';
import I from 'immutable';
import IPropTypes from 'react-immutable-proptypes';
import _ from 'lodash';

import {PropTypes as RPropTypes} from 'react';
// import {TransitionMotion, spring} from 'react-motion';

import EditorToken from './editor_token';
import SymbolTokens from './symbol_token';
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
		onUpdate: RPropTypes.func,
		position: RPropTypes.number,
		reorderTokensEditor: RPropTypes.func,
		textElement: RPropTypes.func,
		value: RPropTypes.string,
	};

	static buildNewToken(key, meta) {
		let token = I.fromJS({
			key,
			index: Date.now(),
		});

		if (meta) {
			token = token.set('args', meta.get('fields').map(f => {
				let arg = null;
				if (f.get('ui_element') == "SelectField") {
					arg = f.getIn(['choices', 0, 0]);
				}
				else {
					arg = f.get('initial');
				}

				return `${arg}`;
			}));
		}

		return token;
	}

	static connectToken(created, prev, next) {
		if (prev == null) prev = I.fromJS({key: "__AND__"});
		if (next == null) next = I.fromJS({key: "__AND__"});

		let isCreatedUnitToken = !_.has(this.connectorMap,
			created.get('key'));

		let prevRequiresConnector = !_.has(this.connectorMap,
			prev.get('key')) || (prev.get('key') == "__RPARENS__");

		let nextRequiresConnector = !_.has(this.connectorMap,
			next.get('key')) || (next.get('key') == "__LPARENS__");

		let tokens = [created];

		if (isCreatedUnitToken && prevRequiresConnector) {
			tokens.splice(0, 0, I.fromJS({
				key: "__AND__",
				index: Date.now() + Math.floor(Math.random() * 100 + 10),
			}));
		}

		if (isCreatedUnitToken && nextRequiresConnector) {
			tokens.splice(tokens.length, 0, I.fromJS({
				key: "__AND__",
				index: Date.now() + Math.floor(Math.random() * 100 + 111),
			}));
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
		let diff = this.areExprsDiff(prevProps.expression,
			this.props.expression);

		if (diff) {
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
		const effectiveValue = this.props.value + ev.target.value;

		this.editorValue = ev.target.value;

		return this.props.onChange({target: {value: effectiveValue}});
	}

	get editorValue() {
		return this.state.editorValue;
	}

	set editorValue(value) {
		this.setState({editorValue: value});
	}

	handleSort = (dragged, over, overOffset) => {
		if (dragged == over) return;

		let initOrder = this.props.expression.map(obj => obj.get('index'));

		initOrder = initOrder.insert(this.props.position, '__EDITOR__');

		let [overPos] = initOrder.findEntry(v => v == over);
		let [draggedPos] = initOrder.findEntry(v => v == dragged);

		if (draggedPos < overPos) overPos--;

		overPos += overOffset;

		let finalOrder = initOrder.remove(draggedPos).insert(overPos, dragged);

		if (!I.is(initOrder, finalOrder)) {
			this.props.reorderTokensEditor(finalOrder.toArray());
		}
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
				onSearch: this.props.onSearch,
				onSort: this.handleSort,
				setEditorValue: v => this.editorValue = v,
				textElement: this.props.textElement,
				token: obj,
			};

			if (_.has(SymbolTokens, key)) {
				let tokenCls = SymbolTokens[key];

				return React.createElement(tokenCls, {
					...props,
					key: `token_${id}`,
					sortData: `${id}`,
					ref: t => this.tokenObjects.push(t),
				});
			}
			else return (
				<UnitToken
					{...props}
					key={`token_${id}`}
					ref={t => this.tokenObjects.push(t)}
					sortData={`${id}`}
				/>
			);
		}).toJS()});

		this.props.onUpdate();
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
					// opacity: spring(1, {precision: 0.1}),
					// left: spring(0, {precision: 10}),
				},
		}));

		styles.splice(this.props.position, 0, {
			key: "editor_token",
			style: {},
			data: React.createElement(EditorToken, {
				deleteToken: this.props.deleteTokenEditor,
				disabled: this.shouldDisable,
				expressionSize: this.props.expression.size,
				inputProps: this.inputProps,
				insertToken: this.props.createTokenEditor,
				isFocused: this.props.isFocused,
				move: this.props.moveTokenEditor,
				setEditorValue: v => this.editorValue = v,
				onSearch: this.props.onSearch,
				onSort: this.handleSort,
				position: this.props.position,
				ref: c => this.editorToken = (c) ?
					c.getDecoratedComponentInstance() :
					null,
				sortData: "__EDITOR__",
				units: this.props.fieldsets,
				value: this.editorValue,
			}),
		});

		return (
			<div
				onTouchTap={ev => {
					if (ev.target == this.mainEditingArea.element) {
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
				{Array.from(styles.map(s =>
					React.cloneElement(s.data, {
						// style: s.style,
						key: s.key,
					})
				))}
			</div>
		);

		// return (
		// 	<TransitionMotion
		// 		styles={styles}
		// 		willEnter={() => ({
		// 			opacity: 0,
		// 			left: -100,
		// 		})}
		// 		willLeave={() => ({
		// 			opacity: spring(0, {precision: 0.1}),
		// 			left: spring(100, {precision: 10}),
		// 		})}
		// 	>
		// 		{styles =>
		// 		}
		// 	</TransitionMotion>
		// );
	}

}
