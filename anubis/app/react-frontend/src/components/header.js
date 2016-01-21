import React from 'react';
import {connect} from 'react-redux';
import {AppBar} from 'material-ui'

let getStateProps = state => ({
	appTitle: state.getIn(['applicationData', 'title'])
});

@connect(getStateProps)
export default class Header extends React.Component {
	render() {
		return (
			<AppBar title={this.props.appTitle} />
		)
	}
}

