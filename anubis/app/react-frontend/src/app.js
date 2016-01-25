import React from 'react';
import {connect} from 'react-redux';
import {Paper, RaisedButton} from 'material-ui';
import Actions from './actions';
import Header from './components/header';
import Footer from './components/footer';
import {Link, RouteHandler} from 'react-router';

let getStateProps = state => ({
	routing: state.get('routing'),
	baseURL: state.getIn(['applicationData', 'baseURL']),
	detailsHtml: state.getIn(['applicationData', 'detailsHtml'])
});

@connect(getStateProps)
export default class App extends React.Component {
	detailsHtml(model, id) {
		return eval("`" + this.props.detailsHtml + "`");
	}

	render() {
		return (
			<div>
				<Header />

				<div style={{padding: "20px"}}>
					<Link to={this.detailsHtml("sessoes", 15748)}>
						<RaisedButton
							label="Sessão 15748"
							primary={true} />
					</Link>
				</div>

				<div>{this.props.children}</div>

				<Footer />

			</div>
		);
	}
}

