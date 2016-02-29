import React from 'react';
import I from 'immutable';
import AppTheme from 'material-ui/lib/styles/raw-themes/light-raw-theme';
import ThemeManager from 'material-ui/lib/styles/theme-manager';

import {Paper, RaisedButton, Dialog, Snackbar} from 'material-ui';
import {connect} from 'react-redux';
import {Link} from 'react-router';
import {bindActionCreators} from 'redux';

import Actions from 'actions';
import Header from 'components/header';
import Footer from 'components/footer';
import TokenField from 'components/TokenField';


let getStateProps = state => ({
	appTheme: state.getIn(['templates', 'appTheme']),
	routing: state.get('routing'),
	baseURL: state.getIn(['applicationData', 'baseURL']),
	detailsHtml: state.getIn(['applicationData', 'detailsHtml']),
	searchHtml: state.getIn(['applicationData', 'searchHtml']),
	globalError: state.getIn(['applicationData', 'globalError']),
	showErrorDetails: state.getIn(['applicationData', 'showErrorDetails']),
});

let getDispatchProps = dispatch => ({
	clearGlobalError: bindActionCreators(Actions.clearGlobalError, dispatch),
	showGlobalErrorDetails: bindActionCreators(Actions.showGlobalErrorDetails,
		dispatch),
});

@connect(getStateProps, getDispatchProps)
export default class App extends React.Component {
	static childContextTypes = {
		muiTheme: React.PropTypes.object,
	}

	getChildContext() {
		return {
			muiTheme: this.theme,
		};
	}

	get theme() {
		return (this.props.appTheme) ?
			ThemeManager.getMuiTheme(this.props.appTheme.toJS()) :
			ThemeManager.getMuiTheme(AppTheme);
	}

	detailsHtml(model, id) {
		return eval("`" + this.props.detailsHtml + "`");
	}

	searchHtml(model, page, sorting, expr) {
		return eval("`" + this.props.searchHtml + "`");
	}

	renderError() {
		let error = this.props.globalError;

		let showErrorDialog = !!error && this.props.showErrorDetails;
		let showErrorSnackbar = !!error && !this.props.showErrorDetails;

		if (!error) error = I.fromJS({traceback: []});

		return (
			<div>
				<Dialog
					title={error.get('name')}
					modal={true}
					open={showErrorDialog}
					autoScrollBodyContent={true}
					actions={
						<RaisedButton
							label="Fechar"
							primary={true}
							onTouchTap={() => this.props.clearGlobalError()}
						/>}
				>
					<p style={{marginBottom: "20px"}}>{error.get('detail')}</p>

					<h4 style={{marginBottom: "20px"}}>Detalhes:</h4>

					<Paper zDepth={1} style={{
						padding: "20px",
						color: this.theme.flatButton.textColor,
						backgroundColor: this.theme.toolbar.backgroundColor
					}}>
						<code style={{
							whiteSpace: "pre-wrap",
							fontFamily: "'Roboto Mono', monospace",
							fontSize: "12pt"
						}}>
							{error.get('traceback').map((line, i) => {
								return <span key={`line_${i}`}>{line}</span>;
							}).toJS()}
						</code>
					</Paper>
				</Dialog>

				<Snackbar
					style={{
						fontFamily: "'Roboto', sans-serif",
						fontSize: "16pt"
					}}
					open={showErrorSnackbar}
					message={`Erro: ${error.get('name')}`}
					action="Detalhes..."
					autoHideDuration={5000}
					onActionTouchTap={() => {
						this.props.showGlobalErrorDetails();
					}}
					onRequestClose={() => this.props.clearGlobalError()}
					/>
			</div>
		);
	}

	render() {
		let searchS = s => this.searchHtml("sessoes", "1", "+realizacao", s);
		let searchV = s => this.searchHtml("volumes", "1", "+ano", s);

		let buttons = [
			[searchS('data,"11/2015"'), "Novembro/15"],
			[searchS('data,"11/2015"/texto_exato,"uber"'),
				"Novembro/15 + Uber"],
			[searchS('data,"12/1980"'), "Dezembro/1980"],
			[searchS('!dados_sessao,"","1",""/data,"11/2015"/(texto_exato,"uber"+texto_exato,"táxi")'), "Pesquisa Complexa"],
		];

		return (
			<div>
				<Header />

				<TokenField params={this.props.params} />

				{this.props.list}
				{this.props.zoom}

				{this.renderError()}

				<Footer />

			</div>
		);
	}
}

