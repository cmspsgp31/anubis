import React from 'react';
import {connect} from 'react-redux';
import {Toolbar, ToolbarGroup, ToolbarTitle} from 'material-ui';

let getStateProps = state => ({
	footer: state.getIn(['applicationData', 'footer'])
});

@connect(getStateProps)
export default class Header extends React.Component {
	render() {
		return (
			<Toolbar style={{position: "fixed", bottom: 0, fontFamily: "'Roboto', sans-serif"}}>
				<ToolbarGroup>
					<ToolbarTitle text={this.props.footer}/>
				</ToolbarGroup>
			</Toolbar>
		)
	}
}


