// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// editor_token.js - token with the editing capabilities for the TokenField.

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
import ReactDOM from 'react-dom';
import Fuse from 'fuse.js';

import {PropTypes as RPropTypes} from 'react';
import IPropTypes from 'react-immutable-proptypes';
import {IconMenu,
    MenuItem,
    Popover,
    Menu} from 'material-ui';
import {ContentLink, ContentAddBox} from 'material-ui/lib/svg-icons';
import {DropTarget} from 'react-dnd';

import Token, {tokenTarget, TokenType} from './token';

const boundTokenTarget = tokenTarget(() => '__EDITOR__');

@DropTarget(TokenType, boundTokenTarget, c => ({dropTarget: c.dropTarget()}))
export default class EditorToken extends Token {
    static propTypes = {
        deleteToken: RPropTypes.func,
        disabled: RPropTypes.bool,
        dropTarget: RPropTypes.func,
        expandDefaultUnit: RPropTypes.func,
        expressionSize: RPropTypes.number,
        inputProps: RPropTypes.shape({
            onBlur: RPropTypes.func.isRequired,
            onChange: RPropTypes.func.isRequired,
            onFocus: RPropTypes.func.isRequired,
            onKeyDown: RPropTypes.func.isRequired,
        }).isRequired,
        insertToken: RPropTypes.func,
        isFocused: RPropTypes.func,
        move: RPropTypes.func,
        onSearch: RPropTypes.func,
        position: RPropTypes.number,
        units: IPropTypes.mapOf({
            choices: IPropTypes.list,
            help_text: RPropTypes.string,
            is_numeric: RPropTypes.bool.isRequired,
            label: RPropTypes.string,
            required: RPropTypes.bool.isRequired,
            ui_element: RPropTypes.string.isRequired,
        }),
        value: RPropTypes.string,
    };

    static contextTypes = {
        muiTheme: RPropTypes.object,
    }

    constructor(props) {
        super(props);

        this.state = {
            open: false,
            completions: [],
            anchor: null,
            selected: null,
        };

        this._forceFocus = false;

    }

    componentWillMount() {
        this.autocompleteOptions = this.generateAutocompleteOptions();
    }

    componentDidUpdate(props) {
        if (props.value != this.props.value) {
            this.buildCompletions(this.props.value);
        }
    }

    generateAutocompleteOptions() {
        const {units} = this.props;

        let source = units.map((obj, key) => ({
            description: obj.get('description'),
            key,
        })).valueSeq().toList();

        source = source.concat(this.connectors.map(([desc, key]) => ({
            description: desc,
            key,
        })));

        return new Fuse(source.toJS(), {
            keys: ['description'],
        });
    }

    renderCloseButton() {
        return null;
    }

    handleBlur = ev => {
        if (this.state.open || this._forceFocus) {
            setTimeout(() => this.lead.focus(), 0);
            this._forceFocus = false;
        }
        else this.props.inputProps.onBlur(ev);
    }

    buildCompletions(text) {
        let completions = [];
        const newState = {};

        this._forceFocus = true;

        if (text != "") {
            completions = this.autocompleteOptions.search(text);

            if (!this.state.anchor) {
                newState.anchor = ReactDOM.findDOMNode(this.lead);
            }
        }

        if (completions.length > 0) {
            const selected = completions[0].key;

            newState.open = true;
            newState.completions = completions;
            newState.selected = selected;
        }
        else {
            newState.open = false;
            newState.selected = null;
            newState.completions = [];
        }

        this.setState(newState);
    }

    handleChange = ev => {
        this.buildCompletions(ev.target.value);

        this.props.inputProps.onChange(ev);
    }

    handleCloseCompletions = () => {
        this._forceFocus = true;
        this.setState({open: false});
    }

    handleFocus = ev => {
        if (ev) this.props.inputProps.onFocus(ev);
    }

    handleKeyDown = ev => {
        switch (ev.which) {
            case 8: // Backspace
                this.handleBackspace();
                break;

            case 37: // Left arrow
                this.handleMoveBack();
                break;

            case 39: // Right arrow
                this.handleMoveForward();
                break;

            case 191: // Numpad star
            case 111: // Forward slash
            case 106: // Forward slash
                this.handleConnector("__AND__");
                ev.preventDefault();
                break;

            case 55: // mainpad 7
            case 56: // mainpad 8
                if (ev.shiftKey) {
                    this.handleConnector("__AND__");
                    ev.preventDefault();
                }
                break;

            case 107: // numpad +
                this.handleConnector("__OR__");
                ev.preventDefault();
                break;

            case 187: // equal
            case 61: // Firefox equal?
            case 220: // backslash
                if (ev.shiftKey) {
                    this.handleConnector("__OR__");
                    ev.preventDefault();
                }
                break;

            case 49: // 1
            case 54: // 6
                if (ev.shiftKey) {
                    this.handleConnector("__NOT__");
                    ev.preventDefault();
                }
                break;

            case 57: // 9
                if (ev.shiftKey) {
                    this.handleConnector("__LPARENS__");
                    ev.preventDefault();
                }
                break;

            case 48: // 0
                if (ev.shiftKey) {
                    this.handleConnector("__RPARENS__");
                    ev.preventDefault();
                }
                break;

            case 27: // ESC
                this.handleCloseCompletions();
                break;

            case 38: // down arrow
                this.handleMoveCompletion(-1);
                break;

            case 40: // down arrow
                this.handleMoveCompletion(1);
                break;

            case 9: // tab
                if (!ev.shiftKey) {
                    this.handleAcceptCompletion(ev);
                }
                break;
        }

        this.props.inputProps.onKeyDown(ev);
    }

    handleMoveBack = () => {
        if (this.props.position > 0) {
            this.props.move(this.props.position - 1);
        }
    }

    handleMoveForward = () => {
        if (this.props.position < this.props.expressionSize) {
            this.props.move(this.props.position + 1);
        }
    }

    handleMoveCompletion = (count) => {
        const keys = this.state.completions.map(({key}) => key);

        if (keys.length == 0) return;

        let current = keys.indexOf(this.state.selected);

        if (current == -1) current = 0;

        let next = current + count;

        if (next >= keys.length) next = 0;
        else if (next < 0) next = keys.length + next;

        this.setState({selected: keys[next]});
    }

    handleBackspace = () => {
        if ((this.props.position > 0) && (this.lead.value.length == 0)) {
            this.props.deleteToken(this.props.position - 1);
        }
    }

    handleConnector = key => {
        if (this.lead.value.length > 0) {
            this.props.expandDefaultUnit(this.lead.value);
        }

        this.handleInsert(key);
    }

    handleInsert = key => {
        this.props.insertToken(key);
    }

    handleAcceptCompletion = ev => {
        if (this.state.selected) {
            this.props.insertToken(this.state.selected);
            this.setState({open: false, selected: null});
            ev.preventDefault();
        }
    }

    connectors = [
            ["E", "__AND__", "/, &, *"],
            ["Ou", "__OR__", "+, |"],
            ["Não", "__NOT__", "!"],
            ["Abre parênteses", "__LPARENS__", "("],
            ["Fecha parênteses", "__RPARENS__", ")"],
    ];

    render() {
        let style = Object.assign({}, this.props.style, {
            height: 24,
            padding: 8,
            marginBottom: 12,
            flexGrow: "1",
            display: "flex",
            justifyContent: "flex-start",
            flexFlow: "row nowrap",
        });

        let inputStyle = Object.assign({}, this.props.style, {
            backgroundColor: "white",
            border: "0px",
            width: "100%",
            height: 16,
            outline: "none",
            verticalAlign: "middle",
            position: "relative",
            display: "inline-block",
            flexGrow: "1",
            userSelect: "all",
        });

        const baseIconColor = this.context.muiTheme.textField.borderColor;
        const focusIconColor = this.context.muiTheme.textField.focusColor;

        const iconColor = this.props.isFocused() ? focusIconColor :
            baseIconColor;

        let units = this.props.units
            .sort((a, b) => a.get('description')
                .localeCompare(b.get('description'), "pt-BR"))
            .map((unit, key) => (
                <MenuItem
                    key={key}
                    onTouchTap={() => this.props.insertToken(key)}
                    primaryText={unit.get('description')}
                    value={key}
                />
            ))
            .valueSeq()
            .toList()
            .toJS();

        let connectors = this.connectors.map(([desc, key, sec]) => (
            <MenuItem
                key={key}
                onTouchTap={() => this.props.insertToken(key)}
                primaryText={desc}
                secondaryText={sec}
                value={key}
            />
        ));

        return this.props.dropTarget(
            <div
                onTouchTap={ev => (this.lead) && (ev.target == this.wrapper) &&
                    this.lead.focus()}
                ref={c => this.wrapper = c}
                style={style}
            >
                <input
                    disabled={this.props.disabled}
                    onBlur={this.handleBlur}
                    onChange={this.handleChange}
                    onFocus={this.handleFocus}
                    onKeyDown={this.handleKeyDown}
                    ref={c => this.lead = c}
                    style={inputStyle}
                    value={this.props.value}
                />

                <Popover
                    anchorEl={this.state.anchor}
                    canAutoPosition={false}
                    onRequestClose={this.handleCloseCompletions}
                    open={this.state.open}
                    useLayerForClickAway={false}
                >
                    <Menu
                        initiallyKeyboardFocused={false}
                        onEscKeyDown={this.handleCloseCompletions}
                        value={this.state.selected}
                    >
                        {this.state.completions.map(({description, key}) => (
                            <MenuItem
                                disableFocusRipple
                                key={key}
                                onTouchTap={() => this.props.insertToken(key)}
                                primaryText={description}
                                value={key}
                            />
                        ))}
                    </Menu>
                </Popover>

                <IconMenu
                    iconButtonElement={this.makeIconButton(ContentLink, {
                        iconProps: {
                            color: iconColor,
                        },
                    })}
                >
                    {connectors}
                </IconMenu>

                <IconMenu
                    iconButtonElement={this.makeIconButton(ContentAddBox, {
                        iconProps: {
                            color: iconColor,
                        },
                    })}
                >
                    {units}
                </IconMenu>


            </div>
        );

    }
}

