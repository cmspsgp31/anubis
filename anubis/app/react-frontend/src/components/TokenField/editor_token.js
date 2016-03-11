import React from 'react';
import ReactDOM from 'react-dom';
import I from 'immutable';
import Fuse from 'fuse.js';

import {PropTypes as RPropTypes} from 'react';
import IPropTypes from 'react-immutable-proptypes';
import {IconMenu,
	MenuItem,
	Popover,
	AutoComplete,
	Menu} from 'material-ui';
import {ContentLink, ContentAddBox} from 'material-ui/lib/svg-icons';
import {DropTarget} from 'react-dnd';

import Token, {tokenTarget, TokenType} from './token';

const boundTokenTarget = tokenTarget(() => '__EDITOR__');

@DropTarget(TokenType, boundTokenTarget, c => ({dropTarget: c.dropTarget()}))
export default class EditorToken extends Token {
	static propTypes = {
		deleteToken: RPropTypes.func,
		disabled: RPropTypes.bool,
		dropTarget: RPropTypes.func,
		expressionSize: RPropTypes.number,
		inputProps: RPropTypes.shape({
			onBlur: RPropTypes.func.isRequired,
			onChange: RPropTypes.func.isRequired,
			onFocus: RPropTypes.func.isRequired,
			onKeyDown: RPropTypes.func.isRequired,
		}).isRequired,
		insertToken: RPropTypes.func,
		isFocused: RPropTypes.func,
		move: RPropTypes.func,
		onSearch: RPropTypes.func,
		position: RPropTypes.number,
		units: IPropTypes.mapOf({
			choices: IPropTypes.list,
			help_text: RPropTypes.string,
			is_numeric: RPropTypes.bool.isRequired,
			label: RPropTypes.string,
			required: RPropTypes.bool.isRequired,
			ui_element: RPropTypes.string.isRequired,
		}),
		value: RPropTypes.string,
	};

	static contextTypes = {
		muiTheme: RPropTypes.object,
	}

	constructor(props) {
		super(props);

		this.state = {
			open: false,
			completions: [],
			anchor: null,
			selected: null,
		};

		this._forceFocus = false;

	}

	componentWillMount() {
		this.autocompleteOptions = this.generateAutocompleteOptions();
	}

	generateAutocompleteOptions() {
		const {units} = this.props;

		let source = units.map((obj, key) => ({
			description: obj.get('description'),
			key,
		})).valueSeq().toList();

		source = source.concat(this.connectors.map(([desc, key]) => ({
			description: desc,
			key,
		})));

		return new Fuse(source.toJS(), {
			keys: ['description'],
		});
	}

	renderCloseButton() {
		return null;
	}

	handleBlur = ev => {
		if (this.state.open || this._forceFocus) {
			this.lead.focus();
			this._forceFocus = false;
		}
		else this.props.inputProps.onBlur(ev);
	}

	handleChange = ev => {
		const text = ev.target.value;
		this._forceFocus = true;

		if (text != "") {
			const completions = this.autocompleteOptions.search(text);

			if (!this.state.anchor) {
				this.setState({anchor: ReactDOM.findDOMNode(this.lead)});
			}

			this.setState({open: true, completions});
		}
		else this.setState({open: false});

		this.props.inputProps.onChange(ev);
	}

	handleCloseCompletions = () => {
		this.setState({open: false});
	}

	handleFocus = ev => {
		if (ev) this.props.inputProps.onFocus(ev);
	}

	handleKeyDown = ev => {
		switch (ev.which) {
			case 8: // Backspace
				this.handleBackspace();
				break;

			case 37: // Left arrow
				this.handleMoveBack();
				break;

			case 39: // Right arrow
				this.handleMoveForward();
				break;

			case 191: // Numpad star
			case 111: // Forward slash
			case 106: // Forward slash
				this.handleInsert("__AND__");
				ev.preventDefault();
				break;

			case 55: // mainpad 7
			case 56: // mainpad 8
				if (ev.shiftKey) {
					this.handleInsert("__AND__");
					ev.preventDefault();
				}
				break;

			case 107: // numpad +
				this.handleInsert("__OR__");
				ev.preventDefault();
				break;

			case 187: // equal
			case 220: // backslash
				if (ev.shiftKey) {
					this.handleInsert("__OR__");
					ev.preventDefault();
				}
				break;

			case 49: // 1
			case 54: // 6
				if (ev.shiftKey) {
					this.handleInsert("__NOT__");
					ev.preventDefault();
				}
				break;

			case 57: // 9
				if (ev.shiftKey) {
					this.handleInsert("__LPARENS__");
					ev.preventDefault();
				}
				break;

			case 48: // 0
				if (ev.shiftKey) {
					this.handleInsert("__RPARENS__");
					ev.preventDefault();
				}
				break;

			case 27: // ESC
				this.handleCloseCompletions();
				break;

			case 38: // down arrow
				this.handleMoveCompletion(-1);
				break;

			case 40: // down arrow
				this.handleMoveCompletion(1);
				break;

			case 9: // tab
				this.handleAcceptCompletion(ev);
				break;
		}

		this.props.inputProps.onKeyDown(ev);
	}

	handleMoveBack = () => {
		if (this.props.position > 0) {
			this.props.move(this.props.position - 1);
		}
	}

	handleMoveForward = () => {
		if (this.props.position < this.props.expressionSize) {
			this.props.move(this.props.position + 1);
		}
	}

	handleMoveCompletion = (count) => {
		let keys = this.state.completions.map(({key}) => key);

		keys.splice(0, 0, null);

		if (keys.length == 0) return;

		let current = keys.indexOf(this.state.selected);

		if (current == -1) current = 0;

		let next = current + count;

		if (next >= keys.length) next = 0;
		else if (next < 0) next = keys.length + next;

		this.setState({selected: keys[next]});
	}

	handleBackspace = () => {
		if ((this.props.position > 0) && (this.lead.value.length == 0)) {
			this.props.deleteToken(this.props.position - 1);
		}
	}

	handleInsert = key => {
		this.props.insertToken(key);
	}

	handleAcceptCompletion = ev => {
		if (this.state.selected) {
			this.props.insertToken(this.state.selected);
			this.setState({open: false, selected: null});
			ev.preventDefault();
		}
	}

	connectors = [
			["E", "__AND__", "/, &, *"],
			["Ou", "__OR__", "+, |"],
			["Não", "__NOT__", "!"],
			["Abre parênteses", "__LPARENS__", "("],
			["Fecha parênteses", "__RPARENS__", ")"],
	];

	render() {
		let style = Object.assign({}, this.props.style, {
			height: 24,
			padding: 8,
			marginBottom: 12,
			flexGrow: "1",
			display: "flex",
			justifyContent: "flex-start",
			flexFlow: "row nowrap",
		});

		let inputStyle = Object.assign({}, this.props.style, {
			border: "0px",
			width: "100%",
			height: 16,
			outline: "none",
			verticalAlign: "middle",
			position: "relative",
			display: "inline-block",
			flexGrow: "1",
			userSelect: "all",
		});

		let baseIconColor = this.context.muiTheme.textField.borderColor;
		let focusIconColor = this.context.muiTheme.textField.focusColor;

		let iconColor = this.props.isFocused() ? focusIconColor : baseIconColor;

		let units = this.props.units
			.sort((a, b) => a.get('description')
				.localeCompare(b.get('description'), "pt-BR"))
			.map((unit, key) => (
				<MenuItem
					key={key}
					onTouchTap={() => this.props.insertToken(key)}
					primaryText={unit.get('description')}
					value={key}
				/>
			))
			.valueSeq()
			.toList()
			.toJS();

		let connectors = this.connectors.map(([desc, key, sec]) => (
			<MenuItem
				key={key}
				onTouchTap={() => this.props.insertToken(key)}
				primaryText={desc}
				secondaryText={sec}
				value={key}
			/>
		));

		return this.props.dropTarget(
			<div
				style={style}
			>
				<input
					disabled={this.props.disabled}
					onBlur={this.handleBlur}
					onChange={this.handleChange}
					onFocus={this.handleFocus}
					onKeyDown={this.handleKeyDown}
					ref={c => this.lead = c}
					style={inputStyle}
					value={this.props.value}
				/>

				<Popover
					onRequestClose={this.handleCloseCompletions}
					open={this.state.open}
					anchorEl={this.state.anchor}
					useLayerForClickAway={false}
				>
					<Menu
						onEscKeyDown={this.handleCloseCompletions}
						initiallyKeyboardFocused={false}
						value={this.state.selected}
					>
						{this.state.completions.map(({description, key}) => (
							<MenuItem
								disableFocusRipple
								onTouchTap={() => this.props.insertToken(key)}
								key={key}
								value={key}
								primaryText={description}
							/>
						))}
					</Menu>
				</Popover>

				<IconMenu
					iconButtonElement={this.makeIconButton(ContentLink, {
						iconProps: {
							color: iconColor,
						},
					})}
				>
					{connectors}
				</IconMenu>

				<IconMenu
					iconButtonElement={this.makeIconButton(ContentAddBox, {
						iconProps: {
							color: iconColor,
						},
					})}
				>
					{units}
				</IconMenu>


			</div>
		);

	}
}

