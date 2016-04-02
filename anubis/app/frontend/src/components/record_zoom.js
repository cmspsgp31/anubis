// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// record_zoom.js - component for zooming in on a record.

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

import React from 'react';
import {PropTypes as RPropTypes} from 'react';
import IPropTypes from 'react-immutable-proptypes';

import {connect} from 'react-redux';
import {Dialog, FlatButton, CircularProgress} from 'material-ui';
import {routeActions} from 'react-router-redux';
import {bindActionCreators} from 'redux';

import Actions from 'actions';

const getStateProps = state => {
    const fullDetails = state.get('details');
    const object = state.getIn(['details', 'object']);
    const modelName = state.getIn(['details', 'model']);
    const modelData = state.getIn(['models', modelName]);
    const detailsApi = state.getIn(['applicationData', 'detailsApi']);
    const detailsHtml = state.getIn(['applicationData', 'detailsHtml']);
    const hasDetails = !!state.get("details");
    const cache = state.getIn(['cache', 'details']);
    const searchHtml = state.getIn(['applicationData', 'searchHtml']);
    const baseURL = state.getIn(['applicationData', 'baseURL']);
    const error = state.getIn(['details', 'error']);
    const appData = state.get('applicationData');

    return {object, modelName, modelData, detailsApi, hasDetails, cache,
            searchHtml, baseURL, fullDetails, error, detailsHtml, appData};
};

const getDispatchProps = dispatch => ({
    goBack: () => dispatch(routeActions.goBack()),
    goTo: url => dispatch(routeActions.push(url)),
    replaceWith: url => dispatch(routeActions.replace(url)),
    fetchDetails: bindActionCreators(Actions.fetchDetails, dispatch),
    restoreDetails: bindActionCreators(Actions.restoreDetails, dispatch),
    clearDetails: bindActionCreators(Actions.clearDetails, dispatch),
    setGlobalError: bindActionCreators(Actions.setGlobalError, dispatch),
});

@connect(getStateProps, getDispatchProps)
export default class RecordZoom extends React.Component {
    static propTypes = {
        alsoSearching: RPropTypes.bool,
        baseURL: RPropTypes.string,
        cache: IPropTypes.map,
        clearDetails: RPropTypes.func,
        detailsApi: RPropTypes.string,
        detailsHtml: RPropTypes.string,
        error: RPropTypes.any,
        fetchDetails: RPropTypes.func,
        fullDetails: IPropTypes.map,
        goTo: RPropTypes.func,
        hasDetails: RPropTypes.bool,
        modelName: RPropTypes.string,
        params: RPropTypes.shape({
            id: RPropTypes.string,
            model: RPropTypes.string,
            page: RPropTypes.string,
            sorting: RPropTypes.string,
            splat: RPropTypes.string,
        }),
        replaceWith: RPropTypes.func,
        restoreDetails: RPropTypes.func,
        searchHtml: React.PropTypes.string,
        setGlobalError: RPropTypes.func,
        templates: React.PropTypes.object,
    };

    static contextTypes = {
        muiTheme: RPropTypes.object,
    }

    constructor(props) {
        super(props);

        this.state = { visible: false };
    }

    componentWillMount() {
        this.setState({visible: true});

        if (!this.props.hasDetails) {
            this.fetchDetails(this.props.params);
        }
        else {
            this.conditionalCache(this.props.params);
        }
    }

    componentDidUpdate(previousProps) {
        if (this.props.error) {
            this.props.setGlobalError(this.props.error);
            if (this.state.visible) this._close();
            return;
        }

        const params = this.props.params;
        const prevParams = previousProps.params;
        let same = (params.model == prevParams.model);

        same = same && (params.id == prevParams.id);

        if (!same) {
            this.props.clearDetails();
            this.fetchDetails(this.props.params);
        }
    }

    componentWillUnmount() {
        if (this.props.hasDetails) this.props.clearDetails();
    }

    get detailsApi() {
        /*eslint-disable no-unused-vars */
        const model = this.props.params.model;
        const id = this.props.params.id;
        /*eslint-enable */

        return eval("`" + this.props.detailsApi + "`");
    }

    get searchHtml() {
        /*eslint-disable no-unused-vars */
        const model = this.props.params.model;
        const expr = this.props.params.splat;
        const page = this.props.params.page;
        const sorting = this.props.params.sorting;
        /*eslint-enable */

        return eval("`" + this.props.searchHtml + "`");
    }

    fetchDetails(params) {
        const model = params.model;
        const id = params.id;

        const cached = (this.props.cache) ?
            this.props.cache.getIn([model, `${id}`]) :
            null;

        if (cached) this.props.restoreDetails(cached);
        else this.props.fetchDetails(this.detailsApi);
    }

    conditionalCache(params) {
        const model = params.model;
        const id = params.id;

        const cached = (this.props.cache) ?
            this.props.cache.getIn([model, `${id}`]) :
            null;

        if (!cached) this.props.restoreDetails(this.props.fullDetails);
    }


    _close() {
        this.setState({visible: false});

        const nav = (this.props.error) ? this.props.replaceWith :
            this.props.goTo;

        window.setTimeout(() => {
            if (this.props.alsoSearching) {
                nav(this.searchHtml);
            }
            else {
                nav(this.props.baseURL);
            }
        }, 450);
    }

    get titleStyle() {
        const muiTheme = this.context.muiTheme;
        const rawTheme = muiTheme.rawTheme;
        const spacing = rawTheme.spacing;
        const gutter = spacing.desktopGutter;

        return {
            margin: 0,
            padding: `${gutter}px ${gutter}px 0 ${gutter}px`,
            color: rawTheme.palette.textColor,
            fontSize: 24,
            fontFamily: "'Roboto', sans-serif",
            lineHeight: '32px',
            fontWeight: 500,
        };
    }

    render() {
        let title = "Carregando...";

        let contents = (
            <div style={{textAlign: "center"}}>
                <CircularProgress
                    mode="indeterminate"
                    size={2}
                />
            </div>
        );

        let actions = [
            <FlatButton
                disabled={!this.props.hasDetails}
                key="close"
                label="Fechar"
                onTouchTap={() => this._close()}
            />,
        ];

        const makeActions = (elems) => (
            <div
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "6px",
                }}
            >
                {elems}
            </div>
        );

        if (this.props.error) {
            contents = <div></div>;
            title = "";
        }
        else if (this.props.hasDetails) {
            let [getTitle, Contents] = this.props.templates[this.props
                .modelName];

            contents = <Contents {...this.props} />;

            title = getTitle(this.props, this.titleStyle,
                             this.context.muiTheme);

            if (Contents.getActions) {
                actions = Contents.getActions(this.props, this.context.muiTheme)
                    .concat(actions);
            }
        }

        if (actions.length == 1) {
            actions = [<div key="empty_action"></div>].concat(actions);
        }

        return (
            <Dialog
            actions={makeActions(actions)}
            autoScrollBodyContent
            key="zoomDialog"
            modal={false}
            onRequestClose={() => this._close()}
            open={this.state.visible}
            style={{zIndex: 10000}}
            title={title}
            >
                {contents}
            </Dialog>
        );
    }
}

