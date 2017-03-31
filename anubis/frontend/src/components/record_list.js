// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// record_list.js - component for listing records that match a search.

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
import I from 'immutable';
import ReactDOM from 'react-dom';
import _ from 'lodash';
import {PropTypes as RPropTypes} from 'react';
import IPropTypes from 'react-immutable-proptypes';

import {connect} from 'react-redux';
import {RaisedButton, Toolbar, ToolbarGroup, CircularProgress, DropDownMenu,
    IconButton, MenuItem, Tabs, Tab, Popover, Menu} from 'material-ui';
import {NavigationArrowUpward, NavigationArrowDownward, NavigationChevronLeft,
    NavigationChevronRight, SocialShare} from 'material-ui/svg-icons';
import {Link} from 'react-router';
import {routeActions} from 'react-router-redux';
import {bindActionCreators} from 'redux';
import {Sticky, StickyContainer} from 'react-sticky';

import Actions from 'actions';

const getStateProps = state => {
    const searchResults = state.get('searchResults');
    const results = state.getIn(['searchResults', 'results']);
    const modelName = state.getIn(['searchResults', 'model']);
    const modelData = state.getIn(['models', modelName]);
    const searchApi = state.getIn(['applicationData', 'searchApi']);
    const searchHtml = state.getIn(['applicationData', 'searchHtml']);
    const searchAndDetailsHtml = state.getIn(['applicationData',
                                              'searchAndDetailsHtml']);
    const isSearch = state.getIn(['searchResults', 'visible']);
    const sorting = state.getIn(['searchResults', 'sorting']);
    const pagination = state.getIn(['searchResults', 'pagination']);
    const selection = state.getIn(['searchResults', 'selection']);
    const actions = state.getIn(['searchResults', 'actions']);
    const cache = state.getIn(['cache', 'searchResults']);
    const baseURL = state.getIn(['applicationData', 'baseURL']);
    const sortingDefaults = state.getIn(['applicationData', 'sortingDefaults']);
    const models = state.get('models');
    const error = state.getIn(['searchResults', 'error']);

    return {results, modelName, modelData, searchApi, searchHtml, isSearch,
            searchAndDetailsHtml, sorting, pagination, selection, cache,
            baseURL, searchResults, models, sortingDefaults, error, actions};
};

const getDispatchProps = dispatch => ({
    fetchSearch: bindActionCreators(Actions.fetchSearch, dispatch),
    restoreSearch: bindActionCreators(Actions.restoreSearch, dispatch),
    clearSearch: bindActionCreators(Actions.clearSearch, dispatch),
    clearSearchCache: bindActionCreators(Actions.clearSearchCache, dispatch),
    setGlobalError: bindActionCreators(Actions.setGlobalError, dispatch),
    goTo: url => dispatch(routeActions.push(url)),
    replaceWith: url => dispatch(routeActions.replace(url)),
    enableEditor: bindActionCreators(Actions.enableEditor, dispatch),
    disableEditor: bindActionCreators(Actions.disableEditor, dispatch),
    startServerAction: bindActionCreators(Actions.startServerAction, dispatch),
    cancelServerAction: bindActionCreators(Actions.cancelServerAction,
                                           dispatch),
    toggleSelectionSearch: bindActionCreators(Actions.toggleSelectionSearch,
                                              dispatch),
});

@connect(getStateProps, getDispatchProps)
export default class RecordList extends React.Component {
    static propTypes = {
        actions: IPropTypes.mapContains({
            title: RPropTypes.string,
            description: RPropTypes.string,
            fields: IPropTypes.listOf(IPropTypes.map),
            models: IPropTypes.listOf(RPropTypes.string),
        }),
        baseURL: RPropTypes.string,
        cache: IPropTypes.map,
        clearSearch: RPropTypes.func,
        clearSearchCache: RPropTypes.func,
        disableEditor: RPropTypes.func,
        enableEditor: RPropTypes.func,
        error: RPropTypes.any,
        fetchSearch: RPropTypes.func,
        goTo: RPropTypes.func,
        isSearch: RPropTypes.bool,
        modelName: RPropTypes.string,
        models: IPropTypes.map,
        pagination: IPropTypes.map,
        params: RPropTypes.shape({
            splat: RPropTypes.string,
            model: RPropTypes.string,
            sorting: RPropTypes.string,
            page: RPropTypes.string,
        }),
        replaceWith: RPropTypes.func,
        restoreSearch: RPropTypes.func,
        results: IPropTypes.listOf(IPropTypes.map),
        searchAndDetailsHtml: RPropTypes.string,
        searchApi: RPropTypes.string,
        searchHtml: RPropTypes.string,
        searchResults: IPropTypes.map,
        selection: IPropTypes.listOf(RPropTypes.string),
        setGlobalError: RPropTypes.func,
        sorting: IPropTypes.map,
        sortingDefaults: IPropTypes.map,
        startServerAction: RPropTypes.func,
        templates: RPropTypes.object,
        toggleSelectionSearch: RPropTypes.func,
    }

    static contextTypes = {
        muiTheme: RPropTypes.object,
    }

    state = {
        showActions: false,
        anchor: null,
    };

    componentWillMount() {
        this.props.enableEditor();

        if (!this.props.isSearch) {
            this.fetchSearch(this.props.params);
        }
        else {
            this.conditionalCache(this.props.params);
        }
    }

    componentDidUpdate(previousProps) {
        this.props.enableEditor();

        if (this.props.error) {
            this.props.setGlobalError(this.props.error);
            this.props.replaceWith(this.props.baseURL);
            return;
        }

        const params = this.props.params;
        const searchParams = [params.model, params.splat, params.sorting,
                            params.page];

        const prevParams = previousProps.params;
        const prevSearchParams = [prevParams.model, prevParams.splat,
                                  prevParams.sorting, prevParams.page];

        const same = _.zipWith(searchParams, prevSearchParams, (a, b) => a == b)
            .every(x => x);

        if (!same) {
            this.props.clearSearch();
            this.fetchSearch(this.props.params);
        }
    }

    componentWillUnmount() {
        this.props.enableEditor();

        if (this.props.isSearch) this.props.clearSearch();
    }

    get searchApi() {
        /*eslint-disable no-unused-vars */
        const model = this.props.params.model;
        const expr = this.props.params.splat;
        const page = this.props.params.page;
        const sorting = this.props.params.sorting;
        /*eslint-enable no-unused-vars*/

        return eval("`" + this.props.searchApi + "`");
    }

    searchAndDetailsHtml(id) {
        /*eslint-disable no-unused-vars */
        const model = this.props.params.model;
        const expr = this.props.params.splat;
        const page = this.props.params.page;
        const sorting = this.props.params.sorting;
        /*eslint-enable no-unused-vars*/

        return eval("`" + this.props.searchAndDetailsHtml + "`");
    }

    searchHtml({model, expr, page, sorting}) {
        model = model || this.props.params.model;
        expr = expr || this.props.params.splat;
        page = page || this.props.params.page;
        sorting = sorting || this.props.params.sorting;

        return eval("`" + this.props.searchHtml + "`");
    }

    fetchSearch(params) {
        const model = params.model || "_default";
        const expr = params.splat;
        const page = params.page || "0";
        const sorting = params.sorting || "+none";

        const cached = (this.props.cache) ?
            this.props.cache.getIn([model, expr, sorting, `${page}`]) :
            null;

        if (cached) this.props.restoreSearch(cached);
        else {
            this.props.disableEditor();
            this.props.fetchSearch(this.searchApi);
        }
    }

    conditionalCache(params) {
        const model = params.model || "_default";
        const expr = params.splat;
        const page = params.page || "0";
        const sorting = params.sorting || "+none";

        const cached = (this.props.cache) ?
            this.props.cache.getIn([model, expr, sorting, `${page}`]) :
            null;

        if (!cached) this.props.restoreSearch(this.props.searchResults);
    }


    _clearCache() {
        const model = this.props.params.model || "_default";
        const expr = this.props.params.splat;
        const page = this.props.params.page || "0";
        const sorting = this.props.params.sorting || "+none";

        this.props.clearSearchCache({model, expr, page, sorting});
        this.props.clearSearch();
        this.props.fetchSearch(this.searchApi);
    }

    goTo(params) {
        this.props.goTo(this.searchHtml(params));
    }

    goToRoot() {
        this.props.goTo(this.props.baseURL);
    }

    _makeSorting({by, ascending}) {
        const prefix = (ascending) ? "+" : "-";

        return `${prefix}${by}`;
    }

    getPaginationElement() {
        if (!this.props.pagination) return null;

        const pagination = this.props.pagination;
        const allPages = pagination.get('allPages');
        const total = pagination.get('recordCount');
        const currentPage = pagination.get('currentPage');
        const prevPage = pagination.get('previousPageNumber');
        const nextPage = pagination.get('nextPageNumber');

        return (
            <ToolbarGroup>
                <IconButton
                    disabled={!prevPage}
                    onTouchTap={() => this.goTo({page: prevPage})}
                    style={{float: "left", top: "3px"}}
                >
                    <NavigationChevronLeft />
                </IconButton>
                <DropDownMenu
                    disabled={total == 0}
                    onChange={(ev, i, value) => this.goTo({page: value})}
                    style={{marginRight: "0px"}}
                    value={`${currentPage}`}
                >
                    {allPages.map(([num, from, to]) => {
                        let text = `Resultados ${from} a ${to} de ${total}`;

                        if (total == 0) {
                            text = "Nenhum resultado encontrado.";
                        }

                        return (
                            <MenuItem
                                key={`${num}`}
                                primaryText={text}
                                value={`${num}`}
                            />
                        );
                    }).toJS()}
                </DropDownMenu>
                <IconButton
                    disabled={!nextPage}
                    onTouchTap={() => this.goTo({page: nextPage})}
                    style={{float: "left", top: "3px"}}
                >
                    <NavigationChevronRight />
                </IconButton>
            </ToolbarGroup>
        );
    }

    getSortingMenu() {
        if (!this.props.sorting.get('available')) return null;

        const available = this.props.sorting.getIn(['available',
                                                    this.props.modelName]);
        const current = this.props.sorting.getIn(['current', 'by']);
        const currentAsc = this.props.sorting.getIn(['current', 'ascending']);

        let upwardColor = (currentAsc) ?
            this.context.muiTheme.flatButton.primaryTextColor :
            this.context.muiTheme.flatButton.textColor;

        let downwardColor = (!currentAsc) ?
            this.context.muiTheme.flatButton.primaryTextColor :
            this.context.muiTheme.flatButton.textColor;

        return (
            <ToolbarGroup>
                <DropDownMenu
                    key="sortSelector"
                    onChange={(ev, i, value) => {
                        const sorting = this._makeSorting({
                            by: value,
                            ascending: currentAsc,
                        });

                        this.goTo({sorting});
                    }}
                    style={{marginRight: "0px"}}
                    value={current}
                >
                    {available.map(([type, desc]) => {
                        return (
                            <MenuItem
                                key={`sort_${type}`}
                                primaryText={desc}
                                value={type}
                            />
                        );
                    }).toJS()}
                </DropDownMenu>
                <IconButton
                    key="sortAsc"
                    onTouchTap={() => {
                        if (!currentAsc) {
                            const sorting = this._makeSorting({
                                by: current,
                                ascending: true,
                            });
                            this.goTo({sorting});
                        }
                    }}
                    style={{float: "left", top: "3px"}}
                >
                    <NavigationArrowUpward
                        color={upwardColor}
                        key="sortAscArrow"
                    />
                </IconButton>
                <IconButton
                    key="sortDesc"
                    onTouchTap={() => {
                        if (currentAsc) {
                            const sorting = this._makeSorting({
                                by: current,
                                ascending: false,
                            });
                            this.goTo({sorting});
                        }
                    }}
                    style={{float: "left", top: "3px"}}
                >
                    <NavigationArrowDownward
                        color={downwardColor}
                        key="sortDescArrow"
                    />
                </IconButton>
            </ToolbarGroup>
        );
    }

    getModelSwitcher() {
        if (this.props.models.size < 2) return null;

        const models = this.props.models
            .map((model, key) => model.set("key", key))
            .toList()
            .sortBy(model => model.get('order'))
            .toJS();

        const selectedModel = this.props.modelName || models[0].key;

        return (
            <Tabs
                onChange={value => this.goTo({
                    model: value,
                    page: "1",
                    sorting: this.props.sortingDefaults.get(value),
                })}
                value={selectedModel}
            >
                {models.map(model =>
                    <Tab
                        key={`switch_to_${model.key}`}
                        label={model.names[1]}
                        value={model.key}
                    />)}
            </Tabs>
        );
    }

    getActionsMenu() {
        if (this.props.actions.size == 0) return null;

        return (
            <ToolbarGroup>
                <RaisedButton
                    label="Ações"
                    onTouchTap={() => this.setState({showActions: true})}
                    ref={c => {
                        if (!this.state.anchor) {
                            const elem = ReactDOM.findDOMNode(c);
                            this.setState({anchor: elem});
                        }
                    }}
                />
                <Popover
                    anchorEl={this.state.anchor}
                    anchorOrigin={{
                        vertical: 'bottom',
                        horizontal: 'left',
                    }}
                    canAutoPosition={false}
                    onRequestClose={() => this.setState({showActions: false})}
                    open={this.state.showActions}
                >
                    <Menu
                        onEscKeyDown={() => this.setState({showActions: false})}
                    >
                        {this.props.actions.map((action, key) =>
                            <MenuItem
                                key={key}
                                onTouchTap={() => {
                                    this.setState({showActions: false});
                                    this.props.startServerAction(key);
                                }}
                                primaryText={action.get('title')}
                            />
                        ).valueSeq().toArray()}
                    </Menu>
                </Popover>

            </ToolbarGroup>
        );
    }

    render() {
        let contents = (
            <div style={{textAlign: "center"}}>
                <CircularProgress
                    size={80}
                    thickness={7}
                />
            </div>
        );

        if (this.props.error) {
            contents = <div></div>;
        }
        else if (this.props.isSearch) {
            let Item = this.props.templates[this.props.modelName];

            let tiles = this.props.results.map(record => {
                const id = record.get('id', null);
                const link = (id) ? this.searchAndDetailsHtml(id) : null;
                const groupName = (!id) ? record.get('__groupName') : null;
                const extraStyle = (Item.getExtraStyle) ?
                    Item.getExtraStyle(record) :
                    {};

                const handleToggleSelect = () => {
                    this.props.toggleSelectionSearch({ids: I.List([`${id}`])});
                };

                const isSelected = (id) ? this.props.selection.toSet()
                    .has(`${id}`) : false;

                return (
                    <li
                        key={`li_${id || groupName}`}
                        style={{
                            minWidth: "200px",
                            margin: "10px",
                            ...extraStyle,
                        }}
                    >
                        <Item
                            goTo={this.props.goTo}
                            groupName={groupName}
                            id_={id}
                            isSelected={isSelected}
                            key={id || groupName}
                            link={link}
                            makeLink={this.searchAndDetailsHtml.bind(this)}
                            record={record}
                            onSelect={handleToggleSelect}
                        />
                    </li>
                );

            }).toJS();

            let pagination = this.getPaginationElement();
            let sorting = this.getSortingMenu();
            let actions = this.getActionsMenu();
            let models = this.getModelSwitcher();

            contents = (
                <div style={{marginBottom: "56px"}}>
                    <Sticky
                        style={{
                            boxShadow: '0 10px 15px 0 rgba(0, 0, 0, 0.4)',
                            position: 'relative',
                            zIndex: 1500,
                            marginBottom: 10,
                        }}
                    >
                        {models}
                        <Toolbar
                            style={{
                                display: "flex",
                                justifyContent: "space-around",
                                alignItems: "stretch",
                                flexFlow: "row wrap",
                                height: "",
                                minHeight: "56px",
                            }}
                        >
                            {pagination}
                            {sorting}
                            {actions}
                            <ToolbarGroup lastChild>
                                <RaisedButton
                                    label="Recarregar"
                                    onTouchTap={() => this._clearCache()}
                                    primary
                                />
                                <RaisedButton
                                    label="Limpar"
                                    onTouchTap={() => this.goToRoot()}
                                    secondary
                                    style={{marginLeft: "0px"}}
                                />
                                <Link to={this.searchHtml({})}>
                                    <IconButton style={{top: "3px"}}>
                                        <SocialShare />
                                    </IconButton>
                                </Link>
                            </ToolbarGroup>
                        </Toolbar>
                    </Sticky>
                    <StickyContainer>
                        <ul
                            style={{
                                display: "flex",
                                flexFlow: "row wrap",
                                listStyle: "none",
                                paddingBottom: 10,
                            }}
                        >
                            {tiles}
                        </ul>
                    </StickyContainer>
                </div>
            );
        }

        return contents;
    }
}
