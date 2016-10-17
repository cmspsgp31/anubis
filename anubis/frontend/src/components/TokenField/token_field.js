// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// token_field.js - the TokenField component.

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


/* eslint-disable react/no-string-refs */
import React from 'react';
import IPropTypes from 'react-immutable-proptypes';
import DnDBackend from 'react-dnd-html5-backend';

import {DragDropContext} from 'react-dnd';
import {connect} from 'react-redux';
import {TextField} from 'material-ui';
import {PropTypes as RPropTypes} from 'react';
import {bindActionCreators} from 'redux';
import {routeActions} from 'react-router-redux';

import TokenList from './token_list';
import TokenSelector from './token_selector';
import Actions from 'actions';

const getStateProps = state => ({
    defaultModel: state.getIn(['applicationData', 'defaultModel']),
    modelName: state.getIn(['searchResults', 'model']),
    models: state.get('models'),
    searchHtml: state.getIn(['applicationData', 'searchHtml']),
    shouldSearch: state.getIn(['tokenEditor', 'shouldSearch']),
    sortingDefaults: state.getIn(['applicationData', 'sortingDefaults']),
    tokenListStateProps: {
        canSearch: state.getIn(['tokenEditor', 'canSearch']),
        defaultFilter: state.getIn(['applicationData', 'defaultFilter']),
        expression: state.getIn(['searchResults', 'expression']),
        fieldsets: state.getIn(['tokenEditor', 'fieldsets']),
        position: state.getIn(['searchResults', 'position']),
    },
    textExpression: state.getIn(['searchResults', 'textExpression']),
});

const getDispatchProps = dispatch => ({
    buildTextExprEditor: bindActionCreators(Actions.buildTextExprEditor,
        dispatch),
    goTo: url => dispatch(routeActions.push(url)),
    toggleSearchEditor: bindActionCreators(Actions.toggleSearchEditor,
        dispatch),
    tokenListDispatchProps: {
        modifyInnerFieldEditor: bindActionCreators(
            Actions.modifyInnerFieldEditor, dispatch),
        moveTokenEditor: bindActionCreators(Actions.moveTokenEditor, dispatch),
        createTokenEditor: bindActionCreators(Actions.createTokenEditor,
            dispatch),
        deleteTokenEditor: bindActionCreators(Actions.deleteTokenEditor,
            dispatch),
        expandDefaultUnitEditor: bindActionCreators(
            Actions.expandDefaultUnitEditor, dispatch),
        reorderTokensEditor: bindActionCreators(Actions.reorderTokensEditor,
            dispatch),
    },
});

@DragDropContext(DnDBackend)
@connect(getStateProps, getDispatchProps)
export default class TokenField extends React.Component {
    static propTypes = {
        buildTextExprEditor: RPropTypes.func,
        defaultModel: RPropTypes.string,
        goTo: RPropTypes.func,
        modelName: RPropTypes.string,
        models: IPropTypes.mapOf({
            names: IPropTypes.listOf(RPropTypes.string),
            order: RPropTypes.number,
        }),
        params: RPropTypes.shape({
            splat: RPropTypes.string,
            model: RPropTypes.string,
            sorting: RPropTypes.string,
            page: RPropTypes.string,
        }),
        searchHtml: RPropTypes.string,
        shouldSearch: RPropTypes.bool,
        sortingDefaults: IPropTypes.map,
        textExpression: RPropTypes.string,
        toggleSearchEditor: RPropTypes.func,
        tokenListDispatchProps: RPropTypes.object,
        tokenListStateProps: RPropTypes.object,
    }

    componentDidUpdate(prevProps) {
        if (this.props.shouldSearch && !prevProps.shouldSearch) {
            this.props.toggleSearchEditor();
            if (this.props.textExpression != "") {
                this.props.goTo(this.searchHtml);
            }
        }
    }

    /*eslint-disable no-unused-vars */
    get searchHtml() {
        const expr = this.props.textExpression;
        const model = this.props.modelName;
        const page = 1;
        const sorting = this.props.params.sorting ||
            this.props.sortingDefaults.get(model);

        return eval("`" + this.props.searchHtml + "`");
    }
    /*eslint-enable no-unused-vars */

    focus = () => {
        this.textField.focus();
    }

    isFocused = () => {
        return (this.textField == undefined) ?
            false :
            this.textField.state.isFocused;
    }

    handleSearch = ev => {
        if (ev) ev.preventDefault();

        const editorValue = (this.textField) &&
            this.textField.input.state.editorValue;

        if (editorValue && (editorValue != "")) {
            this.props.tokenListDispatchProps
                .expandDefaultUnitEditor(editorValue);

            this.textField.input.editorToken.lead.value = "";
            this.textField.input.setState({editorValue: ""});

            this.props.buildTextExprEditor();
        }


        this.props.toggleSearchEditor();
    }

    handleUpdate = () => {
        this.props.buildTextExprEditor();
    }

    render() {
        return (
            <div
                style={{
                    display: "flex",
                    flexFlow: "rows nowrap",
                    justifyContent: 'space-around',
                }}
            >
                <div
                    style={{
                        width: "70%",
                        margin: "0 auto 20px auto",
                    }}
                >
                    <TextField
                        floatingLabelText="Digite aqui sua pesquisa"
                        multiLine
                        ref={c => this.textField = c}
                        style={{
                            width: "100%",
                            height: "",
                            minHeight: "72px",
                        }}
                        value={this.props.textExpression}
                    >
                        <TokenList
                            {...this.props.tokenListStateProps}
                            {...this.props.tokenListDispatchProps}
                            focus={this.focus}
                            isFocused={this.isFocused}
                            onSearch={this.handleSearch}
                            onUpdate={this.handleUpdate}
                            textElement={() => this.textField}
                            value={this.props.textExpression}
                        />
                    </TextField>
                </div>

                <TokenSelector
                    onSearch={this.handleSearch}
                />
            </div>
        );
    }
}

