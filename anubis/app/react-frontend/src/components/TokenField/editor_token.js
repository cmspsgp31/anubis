import React from 'react';

import {PropTypes as RPropTypes} from 'react';
import IPropTypes from 'react-immutable-proptypes';
import {IconMenu, MenuItem} from 'material-ui';
import {ContentLink, ContentAddBox} from 'material-ui/lib/svg-icons';

import Token from './token';


export default class EditorToken extends Token {
	static propTypes = {
		deleteToken: RPropTypes.func,
		disabled: RPropTypes.bool,
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
	};

	static contextTypes = {
		muiTheme: RPropTypes.object,
	}

	renderCloseButton() {
		return null;
	}

	handleBlur = ev => {
		this.props.inputProps.onBlur(ev);
	}

	handleChange = ev => {
		this.props.inputProps.onChange(ev);
	}

	handleFocus = ev => {
		this.props.inputProps.onFocus(ev);
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

	handleBackspace = () => {
		if ((this.props.position > 0) && (this.lead.value.length == 0)) {
			this.props.deleteToken(this.props.position - 1);
		}
	}

	handleInsert = key => {
		this.props.insertToken(key);
	}

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

		let connectors = [
			["E", "__AND__", "/, &, *"],
			["Ou", "__OR__", "+, |"],
			["Não", "__NOT__", "!"],
			["Abre parênteses", "__LPARENS__", "("],
			["Fecha parênteses", "__RPARENS__", ")"],
		].map(([desc, key, sec]) => (
			<MenuItem
				key={key}
				onTouchTap={() => this.props.insertToken(key)}
				primaryText={desc}
				secondaryText={sec}
				value={key}
			/>
		));

		return (
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

