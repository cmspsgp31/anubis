// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// header.js - the header component of the search interface.

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


import React, {PropTypes as RPropTypes} from 'react';
import {connect} from 'react-redux';
import {AppBar} from 'material-ui';

const getStateProps = state => ({
    appTitle: state.getIn(['applicationData', 'title']),
});

@connect(getStateProps)
export default class Header extends React.Component {
    static propTypes = {
        appTitle: RPropTypes.string,
        onRequestToggle: RPropTypes.func.isRequired,
    }

    handleMenu = ev => {
        this.props.onRequestToggle(ev);
    }

    render() {
        return (
            <AppBar
                onLeftIconButtonTouchTap={this.handleMenu}
                title={this.props.appTitle}
            />
        );
    }
}

