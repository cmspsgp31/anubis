import React, {PropTypes as RPropTypes} from 'react';
import {connect} from 'react-redux';
import {AppBar} from 'material-ui';

let getStateProps = state => ({
	appTitle: state.getIn(['applicationData', 'title']),
});

@connect(getStateProps)
export default class Header extends React.Component {
	static propTypes = {
		appTitle: RPropTypes.string,
		onRequestToggle: RPropTypes.func.isRequired,
	}

	handleMenu = ev => {
		this.props.onRequestToggle(ev);
	}

	render() {
		return (
			<AppBar
				onLeftIconButtonTouchTap={this.handleMenu}
				title={this.props.appTitle}
			/>
		);
	}
}

