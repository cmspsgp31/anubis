import React from 'react';
import I from 'immutable';
import {connect} from 'react-redux';
import {Dialog, RaisedButton, CircularProgress} from 'material-ui';
import {routeActions} from 'redux-simple-router';
import {bindActionCreators} from 'redux';

import Actions from '../actions';

let getStateProps = state => {
	let object = state.getIn(['details', 'object']);
	let model_name = state.getIn(['details', 'model']);
	let model_data = state.getIn(['models', model_name]);
	let detailsApi = state.getIn(['applicationData', 'detailsApi']);
	let hasDetails = !!state.get("details");
	let cache = state.getIn(['cache', 'details']);

	return {object, model_name, model_data, detailsApi, hasDetails, cache};
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
		};
	}

	componentWillUnmount() {
		if (this.props.hasDetails) this.props.clearDetails();
	}

	render() {
		let id = (this.props.object) ? this.props.object.get('id') : null;

		let contents = (this.props.hasDetails) ?
			<div>
				<p>Model: {JSON.stringify(this.props.model_data)}</p>
				<p>{JSON.stringify(this.props.object)}</p>
			</div>
			: <div style={{textAlign: "center"}}>
				<CircularProgress mode="indeterminate" size={2}/>;
			</div>

		return (
			<Dialog
				title={this.props.hasDetails && ("Id: " + id) || ("Carregando")}
				modal={true}
				open={true}
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

