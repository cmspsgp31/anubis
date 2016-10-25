// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// extra_component.js - a wrapper for custom user components.

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

import IPropTypes from 'react-immutable-proptypes';

import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';

import Actions from 'actions';

const getStateProps = state => ({
    state,
    modelName: state.getIn(['searchResults', 'model']),
});

const getDispatchProps = dispatch => ({
    performAction: action => bindActionCreators(action, dispatch),
    createTokenEditorWithInitial: bindActionCreators(
        Actions.createTokenEditorWithInitial, dispatch),
});

@connect(getStateProps, getDispatchProps)
export default class ExtraComponent extends React.Component {
    static propTypes = {
        createTokenEditorWithInitial: RPropTypes.func.isRequired,
        modelName: RPropTypes.string.isRequired,
        performAction: RPropTypes.func.isRequired,
        state: IPropTypes.map,
        templates: RPropTypes.object,
    };

    handleCreateToken = (key, ...args) => {
        this.props.createTokenEditorWithInitial({key, args});
    }

    render() {
        const Component = this.props.templates[this.props.modelName];

        return (
            <Component
                actions={Actions}
                onRequestCreateToken={this.handleCreateToken}
                performAction={this.props.performAction}
                state={this.props.state}
            />
        );
    }
}
