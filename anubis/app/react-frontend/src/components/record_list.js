import React from 'react';
import I from 'immutable';
import _ from 'lodash';

import {connect} from 'react-redux';
import {RaisedButton, Toolbar, ToolbarGroup, ToolbarSeparator, CircularProgress,
	IconMenu, FlatButton, DropDownMenu, IconButton, MenuItem, Icons, FontIcon,
	Tabs, Tab } from 'material-ui';
import {ContentSort, NavigationArrowUpward, NavigationArrowDownward,
	SocialShare} from 'material-ui/lib/svg-icons';
import {Link} from 'react-router';
import {routeActions} from 'redux-simple-router';
import {bindActionCreators} from 'redux';

import Actions from 'actions';

let getStateProps = state => {
	let searchResults = state.get('searchResults');
	let results = state.getIn(['searchResults', 'results']);
	let modelName = state.getIn(['searchResults', 'model']);
	let modelData = state.getIn(['models', modelName]);
	let searchApi = state.getIn(['applicationData', 'searchApi']);
	let searchHtml = state.getIn(['applicationData', 'searchHtml']);
	let searchAndDetailsHtml = state.getIn(['applicationData',
		'searchAndDetailsHtml']);
	let isSearch = state.getIn(['searchResults', 'visible']);
	let sorting = state.getIn(['searchResults', 'sorting']);
	let pagination = state.getIn(['searchResults', 'pagination']);
	let selection = state.getIn(['searchResults', 'sorting']);
	let cache = state.getIn(['cache', 'searchResults']);
	let baseURL = state.getIn(['applicationData', 'baseURL']);
	let sortingDefaults = state.getIn(['applicationData', 'sortingDefaults']);
	let models = state.get('models');
	let error = state.getIn(['searchResults', 'error']);

	return {results, modelName, modelData, searchApi, searchHtml, isSearch,
		searchAndDetailsHtml, sorting, pagination, selection, cache, baseURL,
		searchResults, models, sortingDefaults, error};
};

let getDispatchProps = dispatch => ({
	fetchSearch: bindActionCreators(Actions.fetchSearch, dispatch),
	restoreSearch: bindActionCreators(Actions.restoreSearch, dispatch),
	clearSearch: bindActionCreators(Actions.clearSearch, dispatch),
	clearSearchCache: bindActionCreators(Actions.clearSearchCache, dispatch),
	setGlobalError: bindActionCreators(Actions.setGlobalError, dispatch),
	goTo: url => dispatch(routeActions.push(url))
})

@connect(getStateProps, getDispatchProps)
export default class RecordList extends React.Component {
	static contextTypes = {
		muiTheme: React.PropTypes.object,
	}

	get searchApi() {
		let model = this.props.params.model;
		let expr = this.props.params.splat;
		let page = this.props.params.page;
		let sorting = this.props.params.sorting;

		return eval("`" + this.props.searchApi + "`");
	}

	searchAndDetailsHtml(id) {
		let model = this.props.params.model;
		let expr = this.props.params.splat;
		let page = this.props.params.page;
		let sorting = this.props.params.sorting;

		return eval("`" + this.props.searchAndDetailsHtml + "`");
	}

	searchHtml({model, expr, page, sorting}) {
		model = model || this.props.params.model;
		expr = expr || this.props.params.splat;
		page = page || this.props.params.page;
		sorting = sorting || this.props.params.sorting;

		return eval("`" + this.props.searchHtml + "`")
	}

	fetchSearch(params) {
		let model = params.model || "_default";
		let expr = params.splat;
		let page = params.page || "0";
		let sorting = params.sorting || "+none";

		let cached = (this.props.cache) ?
			this.props.cache.getIn([model, expr, sorting, `${page}`]) :
			null;

		if (cached) this.props.restoreSearch(cached);
		else this.props.fetchSearch(this.searchApi);
	}

	conditionalCache(params) {
		let model = params.model || "_default";
		let expr = params.splat;
		let page = params.page || "0";
		let sorting = params.sorting || "+none";

		let cached = (this.props.cache) ?
			this.props.cache.getIn([model, expr, sorting, `${page}`]) :
			null;

		if (!cached) this.props.restoreSearch(this.props.searchResults);
	}

	componentWillMount() {
		if (!this.props.isSearch) {
			this.fetchSearch(this.props.params);
		}
		else {
			this.conditionalCache(this.props.params);
		}
	}

	componentDidUpdate(previousProps) {
		if (this.props.error) {
			this.props.setGlobalError(this.props.error);
			// this.goToRoot();
			return;
		}

		let params = this.props.params;
		let searchParams = [params.model, params.splat, params.sorting,
			params.page];

		let prevParams = previousProps.params;
		let prevSearchParams = [prevParams.model, prevParams.splat,
			prevParams.sorting, prevParams.page];

		let same = _.reduce(
			_.zipWith(searchParams, prevSearchParams, (a, b) => a == b),
			(acc, elem) => acc && elem,
			true
		);

		if (!same) {
			this.props.clearSearch();
			this.fetchSearch(this.props.params);
		}
	}

	componentWillUnmount() {
		if (this.props.isSearch) this.props.clearSearch();
	}

	_clearCache() {
		let model = this.props.params.model || "_default";
		let expr = this.props.params.splat;
		let page = this.props.params.page || "0";
		let sorting = this.props.params.sorting || "+none";

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
		let prefix = (ascending) ? "+" : "-";

		return `${prefix}${by}`;
	}

	getPaginationElement() {
		if (!this.props.pagination) return null;

		let pagination = this.props.pagination;

		let allPages = pagination.get('allPages');
		let total = pagination.get('recordCount');
		let currentPage = pagination.get('currentPage');
		let prevPage = pagination.get('previousPageNumber');
		let nextPage = pagination.get('nextPageNumber');

		return (
			<ToolbarGroup firstChild={true}>
				<IconButton
					onTouchTap={() => this.goTo({page: prevPage})}
					disabled={!prevPage}
					style={{float: "left", top: "3px"}} >
					<Icons.NavigationChevronLeft />
				</IconButton>
				<DropDownMenu
					onChange={(ev, i, value) => this.goTo({page: value})}
					value={`${currentPage}`}
					disabled={total == 0}
					style={{marginRight: "0px"}}>
					{allPages.map(([num, from, to]) => {
						let text = `Resultados ${from} a ${to} de ${total}`;

						if (total == 0) {
							text = "Nenhum resultado encontrado.";
						}

						return (<MenuItem
							key={`${num}`}
							value={`${num}`}
							primaryText={text}
						/>);
					}).toJS()}
				</DropDownMenu>
				<IconButton
					onTouchTap={() => this.goTo({page: nextPage})}
					disabled={!nextPage}
					style={{float: "left", top: "3px"}} >
					<Icons.NavigationChevronRight />
				</IconButton>
			</ToolbarGroup>
		);
	}

	getSortingMenu() {
		if (!this.props.sorting.get('available')) return null;

		let available = this.props.sorting.getIn(['available',
			this.props.modelName]);
		let current = this.props.sorting.getIn(['current', 'by']);
		let currentAsc = this.props.sorting.getIn(['current', 'ascending']);

		let upwardColor = (currentAsc) ?
			this.context.muiTheme.flatButton.primaryTextColor :
			this.context.muiTheme.flatButton.textColor;

		let downwardColor = (!currentAsc) ?
			this.context.muiTheme.flatButton.primaryTextColor :
			this.context.muiTheme.flatButton.textColor;

		return [
			<DropDownMenu
				key="sortSelector"
				value={current}
				style={{marginRight: "0px"}}
				onChange={(ev, i, value) => {
					let sorting = this._makeSorting({by: value,
						ascending: currentAsc});
					this.goTo({sorting});
				}}
				>
					{available.map(([type, desc]) => {
						return (
							<MenuItem key={`sort_${type}`}
								primaryText={desc} value={type} />
						);
					}).toJS()}
			</DropDownMenu>,
			<IconButton
				key="sortAsc"
				style={{float: "left", top: "3px"}}
				onTouchTap={() => {
					if (!currentAsc) {
						let sorting = this._makeSorting({by: current,
							ascending: true});
						this.goTo({sorting});
					}
				}}
				>
					<NavigationArrowUpward key="sortAscArrow"
						color={upwardColor} />
			</IconButton>,
			<IconButton
				key="sortDesc"
				style={{float: "left", top: "3px"}}
				onTouchTap={() => {
					if (currentAsc) {
						let sorting = this._makeSorting({by: current,
							ascending: false});
						this.goTo({sorting});
					}
				}}
				>
					<NavigationArrowDownward key="sortDescArrow"
						color={downwardColor} />
			</IconButton>,
			<ToolbarSeparator key="sortSeparator" style={{marginLeft: "12px"}}/>,
		];
	}

	getModelSwitcher() {
		if (this.props.models.size < 2) return null;

		const models = this.props.models
			.map((model, key) => model.set("key", key))
			.toList()
			.sortBy(model => model.get('order'))
			.toJS();

		let selectedModel = this.props.modelName || models[0].key;

		return (
			<Tabs
				value={selectedModel}
				onChange={value => this.goTo({
					model: value,
					page: "1",
					sorting: this.props.sortingDefaults.get(value)
				})}
			>
				{models.map(model => <Tab
					key={`switch_to_${model.key}`}
					value={model.key}
					label={model.names[1]}
				/>)}
			</Tabs>
		);
	}

	render() {
		let contents = (
			<div style={{textAlign: "center"}}>
				<CircularProgress mode="indeterminate" size={2} />
			</div>
		);

		if (this.props.error) {
			contents = <div></div>;
		}
		else if (this.props.isSearch) {
			let Item = this.props.templates[this.props.modelName];

			let tiles = this.props.results.map(record => {
				let link = this.searchAndDetailsHtml(record.get('id'));
				let id = record.get('id');

				return (
					<li
						key={`li_${id}`}
						style={{
							minWidth: "200px",
							margin: "10px",
							flexGrow: "1",
						}} >
						<Item key={id} record={record}
							link={link} />
					</li>
				);

			}).toJS();

			let pagination = this.getPaginationElement();
			let sorting = this.getSortingMenu();
			let models = this.getModelSwitcher();

			contents = (
				<div style={{marginBottom: "56px"}}>
					{models}
					<Toolbar style={{
							display: "flex",
							justifyContent: "space-between",
							alignItems: "stretch",
							flexFlow: "row wrap"
						}}>
						{pagination}
						<ToolbarGroup lastChild={true}>
							{sorting}
							<RaisedButton
								label="Recarregar"
								primary={true}
								onTouchTap={() => this._clearCache()}
							/>
							<RaisedButton
								label="Limpar"
								style={{marginLeft: "0px"}}
								secondary={true}
								onTouchTap={() => this.goToRoot()}
							/>
							<Link to={this.searchHtml({})}>
								<IconButton
									tooltip="Link"
									style={{top: "3px"}}
								>
									<SocialShare />
								</IconButton>
							</Link>
						</ToolbarGroup>
					</Toolbar>
					<ul style={{
						display: "flex",
						flexFlow: "row wrap",
						listStyle: "none"
					}}>
						{tiles}
					</ul>
				</div>
			);
		}

		return contents;
	}
}
