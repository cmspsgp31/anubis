import React from 'react';
import I from 'immutable';
import {connect} from 'react-redux';
import {RaisedButton,
	Toolbar,
	ToolbarGroup,
	ToolbarSeparator,
	CircularProgress,
	IconMenu,
	DropDownMenu,
	IconButton,
	MenuItem,
	Icons,
} from 'material-ui';
import ContentSort from 'material-ui/lib/svg-icons/content/sort';
import ActionTrendingDown from 'material-ui/lib/svg-icons/action/trending-down';
import ActionTrendingUp from 'material-ui/lib/svg-icons/action/trending-up';
import ToggleCheckBoxOutlineBlank from 'material-ui/lib/svg-icons/toggle/check-box-outline-blank';
import {Link} from 'react-router';
import {routeActions} from 'redux-simple-router';
import {bindActionCreators} from 'redux';

import Actions from '../actions';

let getStateProps = state => {
	let results = state.getIn(['searchResults', 'results']);
	let modelName = state.getIn(['searchResults', 'model']);
	let modelData = state.getIn(['models', modelName]);
	let searchApi = state.getIn(['applicationData', 'searchApi']);
	let searchHtml = state.getIn(['applicationData', 'searchHtml']);
	let detailsHtml = state.getIn(['applicationData', 'detailsHtml']);
	let isSearch = state.getIn(['searchResults', 'visible']);
	let sorting = state.getIn(['searchResults', 'sorting']);
	let pagination = state.getIn(['searchResults', 'pagination']);
	let selection = state.getIn(['searchResults', 'sorting']);
	let cache = state.getIn(['cache', 'searchResults']);
	let baseURL = state.getIn(['applicationData', 'baseURL']);

	return {results, modelName, modelData, searchApi, searchHtml, isSearch,
		detailsHtml, sorting, pagination, selection, cache, baseURL};
};

let getDispatchProps = dispatch => ({
	fetchSearch: bindActionCreators(Actions.fetchSearch, dispatch),
	restoreSearch: bindActionCreators(Actions.restoreSearch, dispatch),
	clearSearch: bindActionCreators(Actions.clearSearch, dispatch),
	clearSearchCache: bindActionCreators(Actions.clearSearchCache, dispatch),
	goTo: url => dispatch(routeActions.push(url))
})

@connect(getStateProps, getDispatchProps)
export default class RecordList extends React.Component {
	get searchApi() {
		let model = this.props.params.model;
		let expr = this.props.params.splat;
		let page = this.props.params.page;
		let sorting = this.props.params.sorting;

		return eval("`" + this.props.searchApi + "`");
	}

	detailsHtml(model, id) {
		return eval("`" + this.props.detailsHtml + "`");
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

	componentWillMount() {
		if (!this.props.isSearch) {
			this.fetchSearch(this.props.params);
		}
	}

	componentDidUpdate(previousProps) {
		if (this.props.params != previousProps.params) {
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
					onTouchTap={() => this.props.goTo(this.searchHtml({page: prevPage}))}
					disabled={!prevPage}
					style={{float: "left", top: "3px"}} >
					<Icons.NavigationChevronLeft />
				</IconButton>
				<DropDownMenu
					onChange={(ev, i, value) => {
						this.props.goTo(this.searchHtml({page: value}))
					}}
					value={`${currentPage}`}
					style={{marginRight: "0px"}}>
					{allPages.map(([num, from, to]) => {
							return (<MenuItem
								key={`${num}`}
								value={`${num}`}
								primaryText={`Registros ${from} a ${to} de ${total}`}
							/>);

					}).toJS()}
				</DropDownMenu>
				<IconButton
					onTouchTap={() => this.props.goTo(this.searchHtml({page: nextPage}))}
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

		return (
			<IconMenu
				value={current}
				iconButtonElement={<IconButton>
					<ContentSort />
				</IconButton>}
				style={{float: "left", top: "3px"}}
				>
					{available.map(([type, desc]) => {
						let selected = type == current;
						let leftIcon = <ToggleCheckBoxOutlineBlank />;
						let rightIcon = <ActionTrendingDown />;

						if (selected) {
							leftIcon = (currentAsc) ?
								<ActionTrendingUp /> :
								<ActionTrendingDown />;

							rightIcon = (!currentAsc) ?
								<ActionTrendingUp /> :
								<ActionTrendingDown />;
						}

						return (
							<MenuItem
								primaryText={desc}
								value={type}
								leftIcon={leftIcon}
								rightIcon={rightIcon}
								/>
						);
					}).toJS()}
			</IconMenu>
		);
	}

	render() {
		let contents = (
			<div style={{textAlign: "center"}}>
				<CircularProgress mode="indeterminate" size={2} />
			</div>
		);

		if (this.props.isSearch) {
			let Item = this.props.templates[this.props.modelName];

			let tiles = this.props.results.map(record => {
				let link = this.detailsHtml(this.props.modelName,
					record.get('id'));
				let id = record.get('id');

				return (
					<li
						key={`li_${id}`}
						style={{
							minWidth: "300px",
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

			contents = (
				<div>
					<Toolbar style={{
							display: "flex",
							justifyContent: "space-between",
							alignItems: "stretch",
							flexFlow: "row wrap"
						}}>
						{pagination}
						<ToolbarGroup lastChild={true}>
							{sorting}
							{sorting &&
								<ToolbarSeparator style={{marginLeft: "12px"}}/>}
							<RaisedButton
								label="Recarregar"
								primary={true}
								onTouchTap={() => this._clearCache()}
							/>
							<RaisedButton
								label="Limpar"
								secondary={true}
								onTouchTap={() => {
									this.props.goTo(this.props.baseURL);
								}}
							/>
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
