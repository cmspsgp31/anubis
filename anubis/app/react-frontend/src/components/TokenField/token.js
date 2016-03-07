import React from 'react';
import ReactDOM from 'react-dom';
import {PropTypes as RPropTypes} from 'react';
import {Paper} from 'material-ui';
import {IconButton} from 'material-ui';
import {ContentClear} from 'material-ui/lib/svg-icons';

export default class Token extends React.Component {
	static propTypes = {
		index: RPropTypes.number,
		onRemove: RPropTypes.func,
		style: RPropTypes.object,
		textElement: RPropTypes.func,
	}

	static contextTypes = {
		muiTheme: RPropTypes.object,
	}

	uppercaseStyle = {
		fontWeight: 500,
		textTransform: 'uppercase',
	};

	get baseStyle() {
		let bgColor = this.context.muiTheme.rawTheme.palette.primary2Color;
		let textBgColor = this.context.muiTheme.rawTheme.palette.
			alternateTextColor;

		return {
			fontSize: 14,
			padding: '8px',
			marginRight: '10px',
			marginBottom: '12px',
			backgroundColor: bgColor,
			color: textBgColor,
			position: 'relative',
			cursor: 'move',
			userSelect: 'none',
		};
	}

	get style() {
		return Object.assign({}, this.baseStyle, this.props.style);
	}

	static expr() {
		return null;
	}

	baseIconButtonStyle = {
		position: "relative",
		display: "inline-block",
		height: 24,
		width: 24,
		padding: 0,
		verticalAlign: "middle",
		marginLeft: 12,
	}

	baseIconButtonIconStyle = {
		height: 18,
		width: 18,
		verticalAlign: "middle",
	}

	makeIconButton(icon, options={style: {}, iconStyle: {}, props: {},
			iconProps: {}}) {
		let style = Object.assign({}, this.baseIconButtonStyle, options.style);

		let iconStyle = Object.assign({}, this.baseIconButtonIconStyle,
			options.iconStyle);

		let props = Object.assign({}, {
			tabIndex: -1,
			iconStyle,
			style,
		}, options.props);

		let iconProps = Object.assign({}, {
			style: iconStyle,
			color: this.style.color,
		}, options.iconProps);

		return React.createElement(IconButton, props, [
			React.createElement(icon, iconProps),
		]);
	}

	renderCloseButton(style = {}, iconStyle = {}) {
		return this.makeIconButton(ContentClear, {
			style,
			iconStyle,
			props: {
				key: "__CLOSE_BUTTON__",
				onClick: () => this.props.onRemove(this.props.index),
			},
		});
	}

	renderContents() {
		return "";
	}

	render() {
		let contents = React.cloneElement(this.renderContents(),
			{key: "__TOKEN_CONTENT__"});

		contents = [contents, this.renderCloseButton()];

		return (
			<div>
				<Paper
					ref={c => this.element = c}
					style={this.style}
					zDepth={1}
				>
					{contents}
				</Paper>
			</div>
		);
	}

}
