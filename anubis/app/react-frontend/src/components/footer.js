import React from 'react';
import {connect} from 'react-redux';
import {Toolbar, ToolbarGroup, ToolbarTitle} from 'material-ui';
import {PropTypes as RPropTypes} from 'react';

let getStateProps = state => ({
	footer: state.getIn(['applicationData', 'footer']),
});

@connect(getStateProps)
export default class Header extends React.Component {
	static propTypes = {
		footer: RPropTypes.string,
	}

	static contextTypes = {
		muiTheme: React.PropTypes.object,
	}

	render() {
		let color = this.context.muiTheme.flatButton.textColor;

		return (
			<Toolbar
				style={{
					position: "fixed",
					bottom: 0,
					fontFamily: "'Roboto', sans-serif",
				}}
			>
				<ToolbarGroup>
					<ToolbarTitle
						style={{color}}
						text={this.props.footer}
					/>
				</ToolbarGroup>
			</Toolbar>
		);
	}
}


