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
	FontIcon,
	MenuItem
} from 'material-ui';
import {Link} from 'react-router';
import {bindActionCreators} from 'redux';

import Actions from '../actions';

let getStateProps = state => {
	let results = state.getIn(['searchResults', 'results']);
	let modelName = state.getIn(['searchResults', 'model']);
	let modelData = state.getIn(['models', modelName]);
	let searchApi = state.getIn(['applicationData', 'searchApi']);
	let detailsHtml = state.getIn(['applicationData', 'detailsHtml']);
	let isSearch = state.getIn(['searchResults', 'visible']);
	let sorting = state.getIn(['searchResults', 'sorting']);
	let pagination = state.getIn(['searchResults', 'pagination']);
	let selection = state.getIn(['searchResults', 'sorting']);
	let cache = state.getIn(['cache', 'searchResults']);

	return {results, modelName, modelData, searchApi, isSearch, detailsHtml,
		sorting, pagination, selection, cache};
};

let getDispatchProps = dispatch => ({
	fetchSearch: bindActionCreators(Actions.fetchSearch, dispatch),
	restoreSearch: bindActionCreators(Actions.restoreSearch, dispatch),
	clearSearch: bindActionCreators(Actions.clearSearch, dispatch),
	clearSearchCache: bindActionCreators(Actions.clearSearchCache, dispatch)
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

	render() {
		let contents = (
			<div style={{textAlign: "center"}}>
				<CircularProgress mode="indeterminate" size={2} />;
			</div>
		);

		if (this.props.isSearch) {
			let Item = this.props.templates[this.props.modelName];

			let tiles = this.props.results.map(record => {
				let link = this.detailsHtml(this.props.modelName,
					record.get('id'));

				return (
					<li
						key={record.id}
						style={{
							minWidth: "300px",
							margin: "10px",
							flexGrow: "1",
						}} >
						<Item record={record}
							link={link} />
					</li>
				);

			}).toJS();

			contents = (
				<div>
					<Toolbar>
						<ToolbarGroup firstChild={true}>
							<DropDownMenu value={1}>
								<MenuItem value={1} primaryText="Página 1 de 3" />
								<MenuItem value={2} primaryText="Página 2 de 3" />
								<MenuItem value={3} primaryText="Página 3 de 3" />
							</DropDownMenu>
							<ToolbarSeparator />
						</ToolbarGroup>
						<ToolbarGroup>
							<RaisedButton
								label="Recarregar"
								primary={true}
								onTouchTap={() => this._clearCache()}
							/>
							<IconMenu iconButtonElement={<FontIcon
									className="muidocs-icon-custom-sort" />}>
								<MenuItem primaryText="Ordem A" />
								<MenuItem primaryText="Ordem B" />
							</IconMenu>
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
