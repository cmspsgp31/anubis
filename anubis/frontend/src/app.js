// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// app.js - main component of the search interface.

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

import React, {PropTypes as RPropTypes} from 'react';
import I from 'immutable';
import IPropTypes from 'react-immutable-proptypes';
import _ from 'lodash';
import AppTheme from 'material-ui/styles/baseThemes/lightBaseTheme';
import getMuiTheme from 'material-ui/styles/getMuiTheme';

import {Paper, RaisedButton, Dialog, Snackbar, ListItem, Divider,
    CircularProgress, Drawer, List, Subheader} from 'material-ui';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {StickyContainer} from 'react-sticky';

import Actions from 'actions';
import Header from 'components/header';
import Footer from 'components/footer';
import TokenField from 'components/TokenField';
import buildField from 'components/build_field';


const getStateProps = state => ({
    appTitle: state.getIn(['applicationData', 'title']),
    appTheme: state.getIn(['templates', 'appTheme']),
    routing: state.get('routing'),
    baseURL: state.getIn(['applicationData', 'baseURL']),
    detailsHtml: state.getIn(['applicationData', 'detailsHtml']),
    searchHtml: state.getIn(['applicationData', 'searchHtml']),
    searchApi: state.getIn(['applicationData', 'searchApi']),
    globalError: state.getIn(['applicationData', 'globalError']),
    showErrorDetails: state.getIn(['applicationData', 'showErrorDetails']),
    actions: state.getIn(['searchResults', 'actions']),
    currentAction: state.getIn(['applicationData', 'currentAction'], null),
    actionResult: state.getIn(['searchResults', 'actionResult']),
    results: state.getIn(['searchResults', 'results']),
    sidebarLinks: state.getIn(['applicationData', 'sidebarLinks']),
    user: state.get('user'),
    modelName: state.getIn(['searchResults', 'model']),
    noUserText: state.get('noUserText'),
});

const getDispatchProps = dispatch => ({
    clearGlobalError: bindActionCreators(Actions.clearGlobalError, dispatch),
    showGlobalErrorDetails: bindActionCreators(Actions.showGlobalErrorDetails,
        dispatch),
    cancelServerAction: bindActionCreators(Actions.cancelServerAction,
        dispatch),
    submitServerAction: bindActionCreators(Actions.submitServerAction,
        dispatch),
});

@connect(getStateProps, getDispatchProps)
export default class App extends React.Component {
    static propTypes = {
        appTheme: IPropTypes.map,
        appTitle: RPropTypes.string,
        extra: RPropTypes.object,
        location: RPropTypes.shape({
            pathname: RPropTypes.string,
        }),
        modelName: RPropTypes.string.isRequired,
        sidebarLinks: IPropTypes.contains({
            admin: RPropTypes.string,
            list: IPropTypes.list,
            login: RPropTypes.string,
            logout: RPropTypes.string,
            title: RPropTypes.string,
        }),
        user: IPropTypes.contains({
            email: RPropTypes.string,
            first_name: RPropTypes.string,
            last_name: RPropTypes.string,
            profile_link: RPropTypes.string,
            username: RPropTypes.string,
        }),
        noUserText: RPropTypes.string,
    }

    static childContextTypes = {
        muiTheme: RPropTypes.object,
    }

    constructor(props) {
        super(props);

        this.state = {
            dataSource: [],
            waiting: false,
            showNav: false,
        };

        this.actionArgs = null;
    }

    getChildContext() {
        return {
            muiTheme: this.theme,
        };
    }

    get theme() {
        return (this.props.appTheme) ?
            getMuiTheme(this.props.appTheme.toJS()) :
            getMuiTheme(AppTheme);
    }

    detailsHtml(model, id) {
        return eval("`" + this.props.detailsHtml + "`");
    }

    searchHtml(model, page, sorting, expr) {
        return eval("`" + this.props.searchHtml + "`");
    }

    get searchApi() {
        /*eslint-disable no-unused-vars */
        const model = this.props.params.model;
        const expr = this.props.params.splat;
        const page = this.props.params.page;
        const sorting = this.props.params.sorting;
        /*eslint-enable no-unused-vars */

        return eval("`" + this.props.searchApi + "`");
    }

    renderError() {
        let error = this.props.globalError;

        const showErrorDialog = !!error && this.props.showErrorDetails;
        const showErrorSnackbar = !!error && !this.props.showErrorDetails;

        if (!error) error = I.Map();

        const traceback = error.get('traceback', null);

        return (
            <div>
                <Dialog
                    actions={
                        <RaisedButton
                            label="Fechar"
                            onTouchTap={() => this.props.clearGlobalError()}
                            primary
                        />
                    }
                    actionsContainerStyle={{borderTop: 'none'}}
                    autoScrollBodyContent
                    modal
                    open={showErrorDialog}
                    title={error.get('name')}
                    titleStyle={{borderBottom: 'none'}}
                >
                    <p style={{marginBottom: "20px"}}>{error.get('detail')}</p>

                    {traceback && (
                        <div>
                            <h4 style={{marginBottom: "20px"}}>
                                {`Detalhes:`}
                            </h4>

                            <Paper
                                style={{
                                    padding: "20px",
                                    color: this.theme.flatButton.textColor,
                                    backgroundColor: this.theme.toolbar.
                                        backgroundColor,
                                }}
                                zDepth={1}
                            >
                                <code
                                    style={{
                                        whiteSpace: "pre-wrap",
                                        fontFamily: "'Roboto Mono', monospace",
                                        fontSize: "12pt",
                                    }}
                                >
                                    {traceback.map((line, i) => (
                                        <span key={`line_${i}`}>
                                            {line}
                                        </span>
                                    )).toJS()}
                                </code>
                            </Paper>
                        </div>
                    )}

                </Dialog>

                <Snackbar
                    action="Detalhes..."
                    autoHideDuration={5000}
                    message={`Erro: ${error.get('name')}`}
                    onActionTouchTap={() => {
                        this.props.showGlobalErrorDetails();
                    }}
                    onRequestClose={() => this.props.clearGlobalError()}
                    open={showErrorSnackbar}
                    style={{
                        fontFamily: "'Roboto', sans-serif",
                        fontSize: "16pt",
                    }}
                />
            </div>
        );
    }

    handleSubmitAction = () => {
        if (!this.props.currentAction) return;
        if (!this.actionArgs) return;

        const actionData = this.props.actions.get(this.props.currentAction);
        const fields = actionData.get('fields');

        const args = new FormData();

        const results = this.props.results.map(result => result.get('id'));

        args.set('object_list', JSON.stringify(results.toArray()));
        args.set('action_name', this.props.currentAction);

        for (const key of fields.keys()) {
            if (_.has(this.actionArgs, key)) {
                args.set(key, this.actionArgs[key]);
            }
        }

        this.props.submitServerAction(this.searchApi, args).then().then(() => {
            this.setState({waiting: false});
        });
        this.setState({waiting: true});
    }

    renderAction() {
        const open = !!this.props.currentAction;

        let actionData = I.fromJS({});

        if (open) {
            actionData = this.props.actions.get(this.props.currentAction);

            if (!this.actionArgs) {
                this.actionArgs = {};
            }
        }
        else {
            this.actionArgs = null;
        }

        const description = actionData.get('description', null);
        const fields = actionData.get('fields', I.Map());
        const hasResult = !!this.props.actionResult;
        const title = actionData.get('title', null);
        const resultSuccess = (hasResult) ?
            this.props.actionResult.get('success') : false;
        const resultError = (hasResult) ?
            this.props.actionResult.get('error') : null;
        const result = (hasResult) ? this.props.actionResult.get('result') :
            null;

        return (
            <Dialog
                actions={
                    <div
                        style={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            padding: "6px",
                        }}
                    >
                        <RaisedButton
                            label={"Fechar"}
                            onTouchTap={this.props.cancelServerAction}
                            secondary
                        />
                        {!hasResult && (
                            <RaisedButton
                                label="OK"
                                onTouchTap={this.handleSubmitAction}
                                primary
                            />
                        )}
                    </div>
                }
                actionsContainerStyle={{borderTop: 'none'}}
                autoScrollBodyContent
                modal
                onRequestClose={this.props.cancelServerAction}
                open={open}
                title={title}
                titleStyle={{borderBottom: 'none'}}
            >
                {this.state.waiting && (
                    <div style={{textAlign: "center"}}>
                        <CircularProgress
                            size={80}
                            thickness={7}
                        />
                    </div>
                ) || (
                    <div>
                        {hasResult && (
                            <div>
                                {resultSuccess
                                && (
                                    <div>
                                        <p>{"Successo"}</p>
                                        <p>{result}
                                        </p>
                                    </div>
                                ) || (
                                    <div>
                                        <p>{"Erro"}</p>
                                        <p>{resultError}</p>
                                    </div>
                                )}
                            </div>
                        ) || (
                            <div>
                                <p>{description}</p>
                                <p>{fields.map((field, key) => (
                                    buildField(field, {
                                        onUpdateInput: searchText => {
                                            let url = field
                                                .get('autocomplete_url');
                                            url += encodeURIComponent(
                                                searchText);

                                            const completion = fetch(url, {
                                                credentials: 'same-origin',
                                            });

                                            completion.then(r => r.json()
                                                .then(json => {
                                                    this.setState({
                                                        dataSource: json,
                                                    });
                                                })
                                            );

                                        },
                                        onSelect: (_, which) => {
                                            this.actionArgs[key] = this.state
                                                .dataSource[which][0];
                                        },
                                        onClearInput: () => {
                                            this.setState({dataSource: []});
                                        },
                                        dataSource: this.state.dataSource.
                                            map(([_, value]) => value),
                                        key,
                                    })
                                )).valueSeq().toArray()}</p>
                            </div>
                        )}
                    </div>
                )}

            </Dialog>
        );
    }

    handleToggleNav = () => {
        this.setState({showNav: !this.state.showNav});
    }

    renderUserInfo() {
        let userShow;

        const firstName = this.props.user.get('first_name', "");

        if (firstName != "") {
            const lastName = this.props.user.get('last_name', "");
            userShow = `${firstName} ${lastName}`;
        }
        else {
            userShow = `${this.props.user.get('username')}`;
        }

        const userEmail = this.props.user.get('email');

        const location = this.props.location.pathname;
        const logoutLink = `${this.props.sidebarLinks.get('logout')}?` +
            `next=` + encodeURIComponent(location);

        let menuItems = [
            {
                text: 'Administração',
                href: this.props.sidebarLinks.get('admin'),
            },
            {
                text: 'Perfil',
                href: this.props.user.get('profile_link'),
            },
            {
                text: 'Alterar senha',
                href: this.props.sidebarLinks.get('password'),
            },
            {
                sep: true,
            },
            {
                text: 'Sair',
                href: logoutLink,
                noBlank: true,
            },
        ];

        menuItems = menuItems.map((item, i) => {
            if (item.sep) {
                return (
                    <ListItem
                            key={`item_${i}`}
                    >
                        <Divider
                            style={{marginLeft: 36}}
                        />
                    </ListItem>
                );
            }

            return (
                <ListItem
                    href={item.href}
                    key={`item_${i}`}
                    style={{paddingLeft: 36}}
                    target={(item.noBlank) ? '' : '_blank'}
                >
                    {item.text}
                </ListItem>
            );
        });

        return (
            <ListItem
                nestedItems={menuItems}
                primaryText={userShow}
                secondaryText={userEmail}
            />
        );
    }

    renderLogin() {
        const location = this.props.location.pathname;
        const loginLink = `${this.props.sidebarLinks.get('login')}?next=` +
            encodeURIComponent(location);

        return (
            <ListItem
                href={loginLink}
                primaryText={`Entrar`}
            />
        );
    }

    renderNoUser() {
        return (
            <ListItem primaryText={this.props.noUserText} />
        );
    }

    render() {
        let navHeader;

        if (I.is(this.props.user, I.Map())) {
            navHeader = this.renderLogin();
        }
        else if (this.props.user === null) {
            navHeader = this.renderNoUser();
        }
        else {
            navHeader = this.renderUserInfo();
        }

        return (
            <div>
                <Header
                    onRequestToggle={this.handleToggleNav}
                />

                <Drawer
                    containerStyle={{zIndex: 9510}}
                    docked={false}
                    onRequestChange={this.handleToggleNav}
                    open={this.state.showNav}
                    overlayStyle={{zIndex: 9500}}
                >
                    <List
                        style={{
                            paddingTop: 48,
                        }}
                    >
                        {navHeader}
                    </List>
                    <Divider />
                    <List>
                        {this.props.sidebarLinks.get('list').map(([t, l]) => (
                            <ListItem
                                primaryText={t}
                                href={l}
                                key={l}
                                target="_blank"
                            />
                        )).unshift((
                            <Subheader key={`__SUBHEADER`}>
                                {this.props.sidebarLinks.get('title')}
                            </Subheader>
                        )).toJS()}
                    </List>
                </Drawer>

                {this.props.extra}

                <TokenField params={this.props.params} />

                <StickyContainer>
                    {this.props.list}
                </StickyContainer>
                {this.props.zoom}

                {this.renderError()}
                {this.renderAction()}

                <Footer />

            </div>
        );
    }
}

