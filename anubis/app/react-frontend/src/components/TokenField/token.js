import React from 'react';
import {PropTypes as RPropTypes} from 'react';
import {Paper} from 'material-ui';

export default class Token extends React.Component {
	static propTypes = {
		style: RPropTypes.object,
	}
	static contextTypes = {
		muiTheme: RPropTypes.object,
	}

	get baseStyle() {
		let bgColor = this.context.muiTheme.rawTheme.palette.primary2Color;
		let textBgColor = this.context.muiTheme.rawTheme.palette.
			alternateTextColor;

		return {
			padding: "6px",
			display: "inline-block",
			marginRight: "6px",
			backgroundColor: bgColor,
			color: textBgColor,
			fontSize: "9pt",
		};
	}

	get style() {
		return Object.assign({}, this.baseStyle, this.props.style);
		// return _.merge(this.baseStyle, this.props.style);
	}

	render() {
		return (
			<Paper
				style={this.style}
				zDepth={1}
			/>
		);
	}

}
