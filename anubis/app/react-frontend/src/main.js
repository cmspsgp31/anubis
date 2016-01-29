import 'babel/polyfill';
import 'whatwg-fetch';

import React from 'react';
import ReactDOM from 'react-dom';
import I from 'immutable';
import Babel from 'babel';
import _ from 'lodash';
import MaterialUI from 'material-ui';
import * as Icons from 'material-ui/lib/svg-icons';
import injectTapEventPlugin from "react-tap-event-plugin";

import {Provider} from 'react-redux';
import {connect} from 'react-redux';
import {Router, Route, browserHistory} from 'react-router';
import {List, ListItem} from 'material-ui';
import {Link} from 'react-router';

import App from 'app';
import configureStore from 'configureStore';
import RecordList from 'components/record_list';
import RecordZoom from 'components/record_zoom';

import {appReducers} from 'reducers/reducer';

window.addEventListener("DOMContentLoaded", () => {
	injectTapEventPlugin();
	let state = window.__AnubisState;
	let appData = state.applicationData;

	let recordTemplates = _.mapValues(state.templates.record, template => {
		let transform = Babel.transform(template, { stage: 0 });
		let code = `((React, MUI, Icons, Link, _) => {
			${transform.code}
			return [getTitle, RecordZoom];
		})(React, MaterialUI, Icons, Link, _)`;

		let [getTitle, contentsCls] = eval(code);

		return [getTitle, contentsCls];
	});

	let searchTemplates = _.mapValues(state.templates.search, template => {
		let transform = Babel.transform(template, { stage: 0 });
		let code = `((React, MUI, Icons, Link, _) => {
			${transform.code}
			return RecordList;
		})(React, MaterialUI, Icons, Link, _)`;

		let contentsCls = eval(code);

		return contentsCls;
	});

	state.templates.appTheme = (template => {
		let transform = Babel.transform(template, { stage: 0 });
		let code = `((Colors, ColorManipulator) => {
			${transform.code}
			return AppTheme;
		})(MaterialUI.Styles.Colors, MaterialUI.Utils.ColorManipulator)`;

		let theme = eval(code);

		return theme;
	})(state.templates.appTheme);

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



