import React, {PropTypes as RPropTypes} from 'react';
import I from 'immutable';
import IPropTypes from 'react-immutable-proptypes';
import _ from 'lodash';
import AppTheme from 'material-ui/lib/styles/raw-themes/light-raw-theme';
import ThemeManager from 'material-ui/lib/styles/theme-manager';

import {Paper, RaisedButton, Dialog, Snackbar, ListItem, Card, Divider,
	CircularProgress, LeftNav, CardMedia, CardTitle, List} from 'material-ui';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {StickyContainer} from 'react-sticky';

import Actions from 'actions';
import Header from 'components/header';
import Footer from 'components/footer';
import TokenField from 'components/TokenField';
import buildField from 'components/build_field';


let getStateProps = state => ({
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
});

let getDispatchProps = dispatch => ({
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
		appTitle: RPropTypes.string,
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
	}

	static childContextTypes = {
		muiTheme: React.PropTypes.object,
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
			ThemeManager.getMuiTheme(this.props.appTheme.toJS()) :
			ThemeManager.getMuiTheme(AppTheme);
	}

	detailsHtml(model, id) {
		return eval("`" + this.props.detailsHtml + "`");
	}

	searchHtml(model, page, sorting, expr) {
		return eval("`" + this.props.searchHtml + "`");
	}

	get searchApi() {
		/*eslint-disable no-unused-vars */
		let model = this.props.params.model;
		let expr = this.props.params.splat;
		let page = this.props.params.page;
		let sorting = this.props.params.sorting;
		/*eslint-enable */

		return eval("`" + this.props.searchApi + "`");
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

	handleSubmitAction = () => {
		if (!this.props.currentAction) return;
		if (!this.actionArgs) return;

		const actionData = this.props.actions.get(this.props.currentAction);
		const fields = actionData.get('fields');

		let args = new FormData();

		const results = this.props.results.map(result => result.get('id'));

		args.set('object_list', JSON.stringify(results.toArray()));
		args.set('action_name', this.props.currentAction);

		for (let key of fields.keys()) {
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
				modal={true}
				onRequestClose={this.props.cancelServerAction}
				open={open}
				autoScrollBodyContent={true}
				title={title}
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
							secondary
							onTouchTap={this.props.cancelServerAction}
						/>
						{!hasResult && (
							<RaisedButton
								label="OK"
								primary
								onTouchTap={this.handleSubmitAction}
							/>
						)}
					</div>
				}
			>
				{this.state.waiting && (
					<div style={{textAlign: "center"}}>
						<CircularProgress mode="indeterminate"
							size={2}
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

											let completion = fetch(url, {
												credentials: 'same-origin',
											});

											completion.then(r => r.json()
													.then(json => {
												this.setState({
													dataSource: json,
												});
											}));

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

		return (
			<ListItem
				nestedItems={[
					<a
						href={this.props.sidebarLinks.get('admin')}
						key={`admin`}
						style={{textDecoration: 'none'}}
						target="_blank"
					>
						<ListItem
							primaryText={`Administração`}
							style={{paddingLeft: 36}}
						/>
					</a>,
					<a
						href={this.props.user.get('profile_link')}
						key={`profile`}
						style={{textDecoration: 'none'}}
						target="_blank"
					>
						<ListItem
							primaryText={`Perfil`}
							style={{paddingLeft: 36}}
						/>
					</a>,
					<a
						href={this.props.sidebarLinks.get('password')}
						key={`password`}
						style={{textDecoration: 'none'}}
						target="_blank"
					>
						<ListItem
							primaryText={`Alterar senha`}
							style={{paddingLeft: 36}}
						/>
					</a>,
					<Divider
						key="sep"
						style={{marginLeft: 36}}
					/>,
					<a
						href={this.props.sidebarLinks.get('logout')}
						key={`logout`}
						style={{textDecoration: 'none'}}
						target="_blank"
					>
						<ListItem
							primaryText={`Sair`}
							style={{paddingLeft: 36}}
						/>
					</a>,
				]}
				primaryText={userShow}
				secondaryText={userEmail}
			/>
		);
	}

	renderLogin() {
		return (
			<a
				href={this.props.sidebarLinks.get('login')}
				style={{textDecoration: 'none'}}
				target="_blank"
			>
				<ListItem
					primaryText={`Entrar`}
				/>
			</a>
		);
	}

	renderNoUser() {
		return (
			<ListItem primaryText="Anubis" />
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

				<LeftNav
					docked={false}
					onRequestChange={this.handleToggleNav}
					open={this.state.showNav}
				>
					<List
						style={{
							paddingTop: 48,
						}}
					>
						{navHeader}
					</List>
					<Divider />
					<List subheader={this.props.sidebarLinks.get('title')}>
						{this.props.sidebarLinks.get('list').map(([t, l]) => (
							<a
								href={l}
								key={l}
								style={{textDecoration: 'none'}}
								target="_blank"
							>
								<ListItem primaryText={t} />
							</a>
						)).toJS()}
					</List>
				</LeftNav>

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

