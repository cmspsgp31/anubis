import React from 'react';
import {connect} from 'react-redux';
import {Paper, RaisedButton} from 'material-ui';
import Actions from './actions';
import {Link} from 'react-router';

@connect(
	state => ({ counter: state.get('counter'), router: state.get('router') }),
	dispatch => {
		return {
			onIncrement: () => dispatch(Actions.increment(1)),
			onDecrement: () => dispatch(Actions.decrement(1)),
		};
})
export default class App extends React.Component {
	static propTypes = {
		counter: React.PropTypes.number.isRequired,
		onIncrement: React.PropTypes.func.isRequired,
		onDecrement: React.PropTypes.func.isRequired,
	}

	render() {
		return (
			<div>
				<div>
					<Paper zIndex={1}>
						<p></p>
						<p>{this.props.counter}</p>
						<p>{this.props.location.pathname}</p>
					</Paper>
				</div>

				<Link to={"/test"}>a</Link>
				<Link to={"/oui"}>b</Link>

				<div>
					<RaisedButton
						label="Increment"
						primary={true}
						onTouchTap={this.props.onIncrement}
					/>

					<RaisedButton
						label="Decrement"
						primary={true}
						onTouchTap={this.props.onDecrement}
					/>
				</div>

				<div>
					{this.props.children}
				</div>
			</div>
		);
	}
}
