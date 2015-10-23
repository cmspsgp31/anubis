import 'babel/polyfill';
import React from 'react';
import ReactDOM from 'react-dom';
import {Provider} from 'react-redux';
import {createStore, applyMiddleware} from 'redux';
import {ReduxRouter} from 'redux-router';
import {Route} from 'react-router';

import injectTapEventPlugin from "npm:react-tap-event-plugin@0.2.1";

import App from './app';
import Reducer from './reducer';
import configureStore from './configureStore';

injectTapEventPlugin();

ReactDOM.render(
	<Provider store={configureStore(Reducer, __AnubisState)}>
		<ReduxRouter>
			<Route path="/" component={App}>
				<Route path="test"><p>test</p></Route>
				<Route path="oui"><p>test</p></Route>
				<Route path="*" />
			</Route>
		</ReduxRouter>
	</Provider>
, document.querySelector("#app"));


