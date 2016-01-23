import 'babel/polyfill';
import React from 'react';
import ReactDOM from 'react-dom';
import I from 'immutable';
import {Provider} from 'react-redux';
import {connect} from 'react-redux';
import {Router, Route, browserHistory} from 'react-router';
import {List, ListItem} from 'material-ui';

import injectTapEventPlugin from "react-tap-event-plugin";

import App from './app';
import {appReducers} from './reducers/reducer.js';
import configureStore from './configureStore';

import RecordList from './components/record_list.js';
import RecordZoom from './components/record_zoom.js';

let getStateProps = s => ({
	routing: s.get('routing'),
	baseURL: s.get('baseURL'),
	isSearch: s.getIn(['searchResults', 'visible']) ? "yes" : "no",
	isDetails: !!s.get('details') ? "yes" : "no",
	results: JSON.stringify(s.getIn(['searchResults', 'results'])),
	details: JSON.stringify(s.getIn(['details', 'object'], null))
})

@connect(getStateProps)
class RouterTest extends React.Component {
	constructor(props) {
		super(props);
	}

	get location() {
		return this.parseSplat(this.props.location.pathname);
	}

	parseSplat(splat) {
		let re = new RegExp(`${this.props.baseURL}\\/(([a-zA-Z][a-zA-Z0-9]*)\\/|)(.*)(\\/(\\d+)|)$`);
		let groups = splat.match(re);

		if (groups) {
			console.log(groups);
			let [_, __, model, search, ___, page] = groups;

			return {model, search, page: ___};
		}
		else return {};
	}

	render() {
		return (
			<div>
				<List zDepth={1}>
					<ListItem
						primaryText="Model"
						secondaryText= {this.location.model} />
					<ListItem
						primaryText="Page"
						secondaryText= {this.location.page} />
					<ListItem
						primaryText="Search Expression"
						secondaryText= {this.location.search} />
				</List>

				<List zDepth={1}>
					<ListItem 
						primaryText="Is search?"
						secondaryText= {this.props.isSearch} />
					<ListItem
						primaryText=""
						secondaryText= {this.props.results} />
				</List>

				<List zDepth={1}>
					<ListItem 
						primaryText="Is details?"
						secondaryText= {this.props.isDetails} />
					<ListItem
						primaryText=""
						secondaryText= {this.props.details} />
				</List>
			</div>
		);
	}
}


window.addEventListener("DOMContentLoaded", () => {
	injectTapEventPlugin();
	let state = window.__AnubisState;
	let store = configureStore(appReducers, state);
	let appData = state.applicationData;
	/*
					<Route path={appData.searchRoute} component={RecordList}>
					</Route>
	 */

	console.log(appData);

	ReactDOM.render(
		<Provider store={store}>
			<Router history={browserHistory}>
				<Route path={appData.baseURL} component={App}>
					<Route path={appData.detailsRoute} component={RecordZoom}>
					</Route>
				</Route>
			</Router>
		</Provider>
	, document.querySelector("#app"));
}, false);



