import 'babel/polyfill';
import React from 'react';
import ReactDOM from 'react-dom';
import I from 'immutable';
import {Provider} from 'react-redux';
import {Router, Route, browserHistory} from 'react-router';
import {List, ListItem} from 'material-ui';

import injectTapEventPlugin from "react-tap-event-plugin";

import App from './app';
import {appReducers} from './reducers/reducer.js';
import configureStore from './configureStore';

class Test1 extends React.Component {
	render() {
		return (
			<div>Test 1</div>
		);
	}
}

class Test2 extends React.Component {
	constructor(props) {
		super(props);

		this.state = I.fromJS({params: {}});
	}

	componentWillMount() {
		console.log(this.props.params.splat);
		this.parseSplat(this.props.params.splat);
	}

	parseSplat(splat) {
		let groups = splat.match(/(.*)\/p(\d+)$/);
		if (groups != null) {
			let [_, search, page] = groups;

			this.state = this.state
				.setIn(["params", "search"], search)
				.setIn(["params", "page"], page);
		}
		else return {};
	}

	render() {
		return (
			<div>Test 2:
				<List zDepth={1}>
				<ListItem primaryText= {this.state.getIn(["params", "search"])} />
				<ListItem primaryText={this.state.getIn(["params", "page"])} />
				</List>
			</div>
		);
	}
}



// window.addEventListener("DOMContentLoaded", () => {
	injectTapEventPlugin();

	ReactDOM.render(
		<Provider store={configureStore(appReducers, __AnubisState)}>
			<Router history={browserHistory}>
				<Route path="/demo.html" component={App}>
					<Route path="test1" component={Test1}></Route>
					<Route path="test2/*" component={Test2}></Route>
				</Route>
			</Router>
		</Provider>
	, document.querySelector("#app"));
// }, false);



