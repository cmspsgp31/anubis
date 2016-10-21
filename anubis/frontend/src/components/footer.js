// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// footer.js - footer component of the search interface.

// This file is part of Anubis.

// Anubis is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// Anubis is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with this program. If not, see <http://www.gnu.org/licenses/>.


import React from 'react';
import {connect} from 'react-redux';
import {Toolbar, ToolbarGroup, ToolbarTitle} from 'material-ui';
import {PropTypes as RPropTypes} from 'react';

const getStateProps = state => ({
    footer: state.getIn(['applicationData', 'footer']),
});

@connect(getStateProps)
export default class Header extends React.Component {
    static propTypes = {
        footer: RPropTypes.string,
    }

    static contextTypes = {
        muiTheme: React.PropTypes.object,
    }

    render() {
        const color = this.context.muiTheme.flatButton.textColor;

        return (
            <Toolbar
                style={{
                    boxShadow: "0 -10px 15px 0 rgba(0,0,0,0.4)",
                    position: "fixed",
                    bottom: 0,
                    width: "100%",
                    fontFamily: "'Roboto', sans-serif",
                    zIndex: 1500,
                }}
            >
                <ToolbarGroup>
                    <ToolbarTitle
                        style={{color}}
                        text={this.props.footer}
                    />
                </ToolbarGroup>
            </Toolbar>
        );
    }
}


