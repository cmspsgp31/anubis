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
	detailsHtml: state.getIn(['applicationData', 'detailsHtml']),
	searchHtml: state.getIn(['applicationData', 'searchHtml'])
});

@connect(getStateProps)
export default class App extends React.Component {
	detailsHtml(model, id) {
		return eval("`" + this.props.detailsHtml + "`");
	}

	searchHtml(model, page, sorting, expr) {
		return eval("`" + this.props.searchHtml + "`");
	}

	render() {
		let linkDetails = this.detailsHtml("sessoes", 15748);
		let linkSearch = this.searchHtml("sessoes", "1", null,
			'data,"11/2015"');
		let linkSearch2 = this.searchHtml("sessoes", "1", null,
			'data,"11/2015"/texto_exato,"uber"');

		return (
			<div>
				<Header />

				<div style={{padding: "20px"}}>
					<Link to={linkDetails}>
						<RaisedButton
							style={{margin: "10px"}}
							label="Sessão 15748"
							primary={true} />
					</Link>

					<Link to={linkSearch}>
						<RaisedButton
							style={{margin: "10px"}}
							label="Novembro/15"
							primary={true} />
					</Link>

					<Link to={linkSearch2}>
						<RaisedButton
							style={{margin: "10px"}}
							label="Novembro/15 + Uber"
							primary={true} />
					</Link>
				</div>

				<div>{this.props.children}</div>

				<Footer />

			</div>
		);
	}
}

