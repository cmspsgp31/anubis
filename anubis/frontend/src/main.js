// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// main.js - search interface entry point.

// This file is part of Anubis.

// Anubis is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// Anubis is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with this program. If not, see <http://www.gnu.org/licenses/>.


import 'babel-polyfill';
import 'whatwg-fetch';
import 'intl';
import 'intl/locale-data/jsonp/pt-BR';

import React from 'react';
import {PropTypes as RPropTypes} from 'react';
import ReactDOM from 'react-dom';
import _ from 'lodash';
import injectTapEventPlugin from "react-tap-event-plugin";

import {Provider} from 'react-redux';
import {Router, Route, browserHistory} from 'react-router';

import App from 'app';
import configureStore from 'configureStore';
import RecordList from 'components/record_list';
import RecordZoom from 'components/record_zoom';

import {appReducers} from 'reducers/reducer';

/* eslint-disable no-unused-vars */
import MaterialUI from 'material-ui';
import * as Icons from 'material-ui/svg-icons';
import {Link} from 'react-router';
/* eslint-enable no-unused-vars */

const compile = (code, vars, returnWhat) => {
    const __COMPILE_MODULES = vars;
    const [names, references] = _.reduce(_.keys(vars),
                                    ([names, references], name) => [
                                        _.concat(names, name),
                                        _.concat(references,
                                            `__COMPILE_MODULES['${name}']`),
                                    ],
                                    [[], []]
                                );

    const transformedCode = `(function (${_.join(names, ", ")}) {
        ${code}
        return ${returnWhat};
    })(${_.join(references, ", ")})`;

    return eval(transformedCode);
};

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
                    <Route
                        component={App}
                        path={appData.baseURL}
                    >
                        <Route
                            components={{zoom: zoomComponent}}
                            path={appData.detailsRoute}
                        />
                        <Route
                            components={{list: searchComponent}}
                            path={appData.searchRoute}
                        />
                        <Route
                            components={{
                                zoom: zoomComponentForSearch,
                                list: searchComponent,
                            }}
                            path={appData.searchAndDetailsRoute}
                        />
                    </Route>
                </Router>
            </Provider>
        );
    }
}


window.addEventListener("DOMContentLoaded", () => {
    injectTapEventPlugin();
    const state = window.__AnubisState;
    const appData = state.applicationData;

    const templateVars = {
        React: require('react'),
        ReactDOM: require('react-dom'),
        MUI: require('material-ui'),
        Icons: require('material-ui/svg-icons'),
        Link: require('react-router')["Link"],
        _: require('lodash'),
        I: require('immutable'),
        Colors: require('material-ui/styles/colors'),
        Sticky: require('react-sticky').Sticky,
    };

    const themeVars = {
        Colors: require('material-ui/styles/colors'),
        ColorManipulator: require('material-ui/utils/colorManipulator'),
    };

    const recordTemplates = _.mapValues(
        state.templates.record,
        template => compile(template, templateVars, "[getTitle, RecordZoom]")
    );

    const searchTemplates = _.mapValues(
        state.templates.search,
        template => compile(template, templateVars, "RecordList")
    );

    state.templates.appTheme = compile(state.templates.appTheme, themeVars,
        "AppTheme");

    let zoomComponent = (props) => (
        <RecordZoom
            {...props}
            alsoSearching={false}
            key="zoomComponent"
            templates={recordTemplates}
        />
    );

    let searchComponent = (props) => (
        <RecordList
            {...props}
            key="searchComponent"
            templates={searchTemplates}
        />
    );

    let zoomComponentForSearch = (props) => (
        <RecordZoom
            {...props}
            alsoSearching
            key="zoomComponent"
            templates={recordTemplates}
        />
    );

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



