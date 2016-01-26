class RecordList extends React.Component {
	render() {
		let id = `ID: ${this.props.record.get('id')}`;
		let items = Array.from(this.props.record.map((value, key) => {
			return (
				<MUI.ListItem key={key}
					primaryText={key}
					secondaryText={JSON.stringify(value)}
					/>
			);
		}).values());

		return (
			<MUI.Card>
				<MUI.CardHeader
					title={<Link to={this.props.link}>{id}</Link>}
					/>
				<MUI.CardText>
					<MUI.List>
						{items}
					</MUI.List>
				</MUI.CardText>
			</MUI.Card>
		);
	}
}

