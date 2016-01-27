import 'babel/polyfill';
import 'whatwg-fetch';
import React from 'react';
import ReactDOM from 'react-dom';
import I from 'immutable';
import {Provider} from 'react-redux';
import {connect} from 'react-redux';
import {Router, Route, browserHistory} from 'react-router';
import {List, ListItem} from 'material-ui';
import MaterialUI from 'material-ui';

import injectTapEventPlugin from "react-tap-event-plugin";

import App from './app';
import {appReducers} from './reducers/reducer.js';
import configureStore from './configureStore';

import RecordList from './components/record_list.js';
import RecordZoom from './components/record_zoom.js';

import Babel from 'babel';
import _ from 'lodash';

import {Link} from 'react-router';

window.addEventListener("DOMContentLoaded", () => {
	injectTapEventPlugin();
	let state = window.__AnubisState;
	let appData = state.applicationData;

	let recordTemplates = _.mapValues(state.templates.record, template => {
		let transform = Babel.transform(template, { stage: 0 });
		let code = `((React, MUI) => {
			${transform.code}
			return [getTitle, RecordZoom];
		})(React, MaterialUI)`;

		let [getTitle, contentsCls] = eval(code);

		return [getTitle, contentsCls];
	});

	let searchTemplates = _.mapValues(state.templates.search, template => {
		let transform = Babel.transform(template, { stage: 0 });
		let code = `((React, MUI, Link) => {
			${transform.code}
			return RecordList;
		})(React, MaterialUI, Link)`;

		let contentsCls = eval(code);

		return contentsCls;
	});

	let zoomComponent = (props) => <RecordZoom {...props}
		key="zoomComponent"
		templates={recordTemplates}
		alsoSearching={false}
		/>;

	let searchComponent = (props) => <RecordList {...props}
		key="searchComponent"
		templates={searchTemplates}
		/>;

	let zoomComponentForSearch = (props) => <RecordZoom {...props}
		key="zoomComponent"
		templates={recordTemplates}
		alsoSearching={true}
		/>;

	let store = configureStore(appReducers, state);

	ReactDOM.render(
		<Provider store={store}>
			<Router history={browserHistory}>
				<Route path={appData.baseURL} component={App}>
					<Route
						path={appData.detailsRoute}
						components={{zoom: zoomComponent}}>
					</Route>
					<Route path={appData.searchRoute}
						components={{list: searchComponent}}>
					</Route>
					<Route path={appData.searchAndDetailsRoute}
						components={{
							zoom: zoomComponentForSearch,
							list: searchComponent
						}}>
					</Route>
				</Route>
			</Router>
		</Provider>
	, document.querySelector("#app"));
}, false);



