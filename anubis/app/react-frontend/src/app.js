import React from 'react';
import {connect} from 'react-redux';
import {Paper, RaisedButton} from 'material-ui';
import Actions from './actions';
import {Link, RouteHandler} from 'react-router';

let getStateProps = state => ({
	counter: state.get('counter'),
	routing: state.get('routing')
});

let getDispatchProps = dispatch => ({
	onIncrement: () => dispatch(Actions.increment(1)),
	onDecrement: () => dispatch(Actions.decrement(1))
});

@connect(getStateProps, getDispatchProps)
export default class App extends React.Component {
	static propTypes = {
		counter: React.PropTypes.number.isRequired,
		onIncrement: React.PropTypes.func.isRequired,
		onDecrement: React.PropTypes.func.isRequired,
	}

	render() {
		let buttons = [
			{ title: "Home"
			, route: "/demo.html"
			},
			{ title: "Test 1"
			, route: "/demo.html/test1"
			},
			{ title: "Test 2"
			, route: `/demo.html/test2/intervalo,"1997","1998"/(tipo_sessao,"1"\+tipo_sessao,"2")/p4`
			}
		];

		return (
			<div>
				<div>
					<Paper zIndex={1}>
						<p></p>
						<p>{this.props.counter}</p>
						<p>{this.props.location.pathname}</p>
					</Paper>
				</div>

				<div style={{ display: "table", borderSpacing: "5px" }}>

					<div style={{display: "tableRow"}}>
						{buttons.map(data => {
							return (
								<Link key={data.route} to={data.route} 
									style={{display: "tableCell",
										padding: "5px"}}>
									<RaisedButton
										primary={true}
										label={data.title} />
								</Link>
							);
						})}
					</div>
				</div>

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

				<div>{this.props.children}</div>

			</div>
		);
	}
}

