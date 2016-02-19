import React from 'react';
import {PropTypes as RPropTypes} from 'react';
import IPropTypes from 'react-immutable-proptypes';

import {connect} from 'react-redux';
import {Dialog, FlatButton, CircularProgress} from 'material-ui';
import {routeActions} from 'react-router-redux';
import {bindActionCreators} from 'redux';

import Actions from 'actions';

let getStateProps = state => {
	let fullDetails = state.get('details');
	let object = state.getIn(['details', 'object']);
	let modelName = state.getIn(['details', 'model']);
	let modelData = state.getIn(['models', modelName]);
	let detailsApi = state.getIn(['applicationData', 'detailsApi']);
	let detailsHtml = state.getIn(['applicationData', 'detailsHtml']);
	let hasDetails = !!state.get("details");
	let cache = state.getIn(['cache', 'details']);
	let searchHtml = state.getIn(['applicationData', 'searchHtml']);
	let baseURL = state.getIn(['applicationData', 'baseURL']);
	let error = state.getIn(['details', 'error']);
	let appData = state.get('applicationData');

	return {object, modelName, modelData, detailsApi, hasDetails, cache,
		searchHtml, baseURL, fullDetails, error, detailsHtml, appData};
};

let getDispatchProps = dispatch => ({
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
		/*eslint-disable react/no-set-state */
		this.setState({visible: true});
		/*eslint-enable */

		if (!this.props.hasDetails) {
			this.fetchDetails(this.props.params)
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

		let params = this.props.params;
		let prevParams = previousProps.params;
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
		let model = this.props.params.model;
		let id = this.props.params.id;
		/*eslint-enable */

		return eval("`" + this.props.detailsApi + "`");
	}

	get searchHtml() {
		/*eslint-disable no-unused-vars */
		let model = this.props.params.model;
		let expr = this.props.params.splat;
		let page = this.props.params.page;
		let sorting = this.props.params.sorting;
		/*eslint-enable */

		return eval("`" + this.props.searchHtml + "`");
	}

	fetchDetails(params) {
		let model = params.model;
		let id = params.id;

		let cached = (this.props.cache) ?
			this.props.cache.getIn([model, `${id}`]) :
			null;

		if (cached) this.props.restoreDetails(cached);
		else this.props.fetchDetails(this.detailsApi);
	}

	conditionalCache(params) {
		let model = params.model;
		let id = params.id;

		let cached = (this.props.cache) ?
			this.props.cache.getIn([model, `${id}`]) :
			null;

		if (!cached) this.props.restoreDetails(this.props.fullDetails);

	}


	_close() {
		/*eslint-disable react/no-set-state */
		this.setState({visible: false});
		/*eslint-enable */

		let nav = (this.props.error) ? this.props.replaceWith :
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
		// let id = (this.props.object) ? this.props.object.get('id') : null;
		let title = "Carregando...";

		let contents = (
			<div style={{textAlign: "center"}}>
				<CircularProgress mode="indeterminate"
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

		let makeActions = (elems) =>
			<div style={{
				display: "flex",
				justifyContent: "space-between",
				alignItems: "center",
				padding: "6px",
			}}
			>{elems}</div>;

		if (this.props.error) {
			contents = <div></div>;
			title = "";
		}
		else if (this.props.hasDetails) {
			let [getTitle, Contents] = this.props.templates[
				this.props.modelName];

			contents = <Contents {...this.props} />;
			title = getTitle(this.props, this.titleStyle,
				this.context.muiTheme);

			if (Contents.getActions) {
				actions = Contents.getActions(this.props,
					this.context.muiTheme).concat(actions);
			}
		}

		if (actions.length == 1) actions = [<div key="empty_action"></div>].
			concat(actions);

		return (
			<Dialog
				actions={makeActions(actions)}
				autoScrollBodyContent
				key="zoomDialog"
				modal={false}
				onRequestClose={() => this._close()}
				open={this.state.visible}
				title={title}
			>
				{contents}
			</Dialog>
		);
	}
}

