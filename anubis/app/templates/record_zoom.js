function getTitle(props, style={}) {
	return (
		<h3 style={style}>
			<a href="#">
				"ID: {props.object.get('id')}"
			</a>
		</h3>
	);
}

class RecordZoom extends React.Component {
	render() {
		return (
			<MUI.List>
				{(() => {
					let rows = [];
					for (let [key, value]
								of this.props.object.entries()) {
						rows.push(<MUI.ListItem key={key}
							primaryText={key}
							secondaryText={value} />
						);
						rows.push(<MUI.Divider
							key={`${key}_divider`}
							inset={true} />
						);
					}
					return rows;
				})()}
			</MUI.List>
		);
	}
}

