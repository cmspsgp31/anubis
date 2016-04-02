import 'babel/polyfill';
import 'whatwg-fetch';
import 'intl';
import 'intl/locale-data/jsonp/pt-BR';

import React from 'react';
import {PropTypes as RPropTypes} from 'react';
import ReactDOM from 'react-dom';
import Babel from 'babel';
import _ from 'lodash';
import MaterialUI from 'material-ui';
import * as Icons from 'material-ui/lib/svg-icons';
import injectTapEventPlugin from "react-tap-event-plugin";

import {Provider} from 'react-redux';
import {Router, Route, browserHistory} from 'react-router';
import {Link} from 'react-router';

import App from 'app';
import configureStore from 'configureStore';
import RecordList from 'components/record_list';
import RecordZoom from 'components/record_zoom';

import {appReducers} from 'reducers/reducer';

function compile(code, vars, returnWhat) {
	let [globals, args] = _.reduce(
		vars,
		([globals, args], global, arg) => [
			_.concat(globals, global), _.concat(args, arg),
		],
		[[], []]
	);

	let transform = Babel.transform(code, {stage: 0});

	let transformedCode = `(function (${_.join(args, ", ")}) {
		${transform.code}
		return ${returnWhat};
	})(${_.join(globals, ", ")})`;

	return eval(transformedCode);
}

class Main extends React.Component {
	static propTypes = {
		appData: RPropTypes.object,
		searchComponent: RPropTypes.func,
		store: RPropTypes.object,
		zoomComponent: RPropTypes.func,
		zoomComponentForSearch: RPropTypes.func,
	}

	render() {
		const {
			appData,
			store,
			zoomComponent,
			zoomComponentForSearch,
			searchComponent,
		} = this.props;

		return (
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
		);
	}
}


window.addEventListener("DOMContentLoaded", () => {
	injectTapEventPlugin();
	let state = window.__AnubisState;
	let appData = state.applicationData;

	let templateVars = {
		React: "React",
		MUI: "MaterialUI",
		Icons: "Icons",
		Link: "Link",
		_: "_"
	};

	let themeVars = {
		Colors: "MaterialUI.Styles.Colors",
		ColorManipulator: "MaterialUI.Utils.ColorManipulator"
	};

	let recordTemplates = _.mapValues(
		state.templates.record,
		template => compile(template, templateVars, "[getTitle, RecordZoom]")
	);

	let searchTemplates = _.mapValues(
		state.templates.search,
		template => compile(template, templateVars, "RecordList")
	);

	state.templates.appTheme = compile(state.templates.appTheme, themeVars,
		"AppTheme");

	let zoomComponent = (props) => <RecordZoom {...props}
		alsoSearching={false}
		key="zoomComponent"
		templates={recordTemplates}
		/>;

	let searchComponent = (props) => <RecordList {...props}
		key="searchComponent"
		templates={searchTemplates}
		/>;

	let zoomComponentForSearch = (props) => <RecordZoom {...props}
		key="zoomComponent"
		templates={recordTemplates}
		alsoSearching
		/>;

	let store = configureStore(appReducers, state);

	ReactDOM.render(
		<Main
			appData={appData}
			searchComponent={searchComponent}
			store={store}
			zoomComponent={zoomComponent}
			zoomComponentForSearch={zoomComponentForSearch}
		/>
	, document.querySelector("#app"));

	window.HistoryWrapper = browserHistory;
}, false);



