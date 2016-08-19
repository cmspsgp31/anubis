class RecordList extends React.Component {
    renderGroup(group) {
        const depth = group.get('__depth');

        const rootGroup = depth == 0;
        const offset = depth * 5;

        let items = null;

        if (group.get('__leaf')) {
            items = group.get('__items').map(record => {
                const id = `ID: ${record.get('id')}`;
                const link = this.props.makeLink(record.get('id'));

                const padding = `${(rootGroup) ? offset : offset + 5}px`;

                return (
                    <li style={{paddingLeft: padding}}>
                        <div><strong><Link to={link}>{id}</Link></strong></div>
                        <MUI.List>
                            {this.renderRecord(record)}
                        </MUI.List>
                    </li>
                );
            }).toJS();
        }
        else {
            items = group
                .get('__items').map(group => this.renderGroup(group))
                .toJS();
        }

        return (
            <div style={{paddingLeft: `${offset}px`}}>
                {(!rootGroup) && (<div>
                    <strong>Group: {group.get('__groupName')}</strong>
                </div>)}
                <ul>
                    {items}
                </ul>
            </div>
        );

    }

    renderRecord(record) {
        const rendered = Array.from(record.map((value, key) => {
            return (
                <MUI.ListItem key={key}
                    primaryText={key}
                    secondaryText={JSON.stringify(value)}
                    />
            );
        }).values());

        return rendered;
    }

    render() {
        let contents = null;
        let title = null;

        if (this.props.id_) {
            const id = `ID: ${this.props.id_}`;
            const fields = this.renderRecord(this.props.record);

            title = <Link to={this.props.link}>{id}</Link>;
            contents = <MUI.List>{fields}</MUI.List>;
        }
        else {
            title = `Group: ${this.props.groupName}`;
            contents = this.renderGroup(this.props.record);
        }

        return (
            <MUI.Card>
                <MUI.CardHeader title={title} />
                <MUI.CardText>
                    {contents}
                </MUI.CardText>
            </MUI.Card>
        );
    }
}

