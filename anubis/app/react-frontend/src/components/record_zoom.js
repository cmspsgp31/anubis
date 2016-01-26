import React from 'react';
import I from 'immutable';
import {connect} from 'react-redux';
import {Dialog, RaisedButton, CircularProgress} from 'material-ui';
import {routeActions} from 'redux-simple-router';
import {bindActionCreators} from 'redux';

import Actions from '../actions';

let getStateProps = state => {
	let object = state.getIn(['details', 'object']);
	let modelName = state.getIn(['details', 'model']);
	let modelData = state.getIn(['models', modelName]);
	let detailsApi = state.getIn(['applicationData', 'detailsApi']);
	let hasDetails = !!state.get("details");
	let cache = state.getIn(['cache', 'details']);

	return {object, modelName, modelData, detailsApi, hasDetails, cache};
};

let getDispatchProps = dispatch => ({
	goBack: () => dispatch(routeActions.goBack()),
	fetchDetails: bindActionCreators(Actions.fetchDetails, dispatch),
	restoreDetails: bindActionCreators(Actions.restoreDetails, dispatch),
	clearDetails: bindActionCreators(Actions.clearDetails, dispatch),
});

@connect(getStateProps, getDispatchProps)
export default class RecordZoom extends React.Component {
	get detailsApi() {
		let model = this.props.params.model;
		let id = this.props.params.id;

		return eval("`" + this.props.detailsApi + "`");
	}

	componentWillMount() {
		if (!this.props.hasDetails) {
			let model = this.props.params.model;
			let id = this.props.params.id;
			let cached = (this.props.cache) ?
				this.props.cache.getIn([model, `${id}`]) :
				null;

			if (cached) this.props.restoreDetails(cached);
			else this.props.fetchDetails(this.detailsApi);
		}
	}

	componentWillUnmount() {
		if (this.props.hasDetails) this.props.clearDetails();
	}

	render() {
		let id = (this.props.object) ? this.props.object.get('id') : null;
		let contents = (
			<div style={{textAlign: "center"}}>
				<CircularProgress mode="indeterminate" size={2}/>;
			</div>
		);
		let title = "Carregando...";

		if (this.props.hasDetails) {
			let [getTitle, Contents] = this.props.templates[
				this.props.modelName];

			contents = <Contents ref="contents" {...this.props} />;
			title = getTitle(this.props, this.getStyles);
		}

		return (
			<Dialog
				title={title}
				modal={true}
				open={true}
				autoScrollBodyContent={true}
				actions={<RaisedButton
					disabled={!this.props.hasDetails}
					label="Fechar"
					primary={true}
					onTouchTap={this.props.goBack} />}>
				{contents}
			</Dialog>
		);
	}
}

