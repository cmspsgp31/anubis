// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// unit_token.js - token representing a unit search.

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
import Intl from 'intl';
import I from 'immutable';
import _ from 'lodash';

import {PropTypes as RPropTypes} from 'react';
import {TextField, SelectField, MenuItem} from 'material-ui';
import DatePickerDialog from 'material-ui/DatePicker/DatePickerDialog';
import {ActionDateRange} from 'material-ui/svg-icons';

import Token, {makeDraggable} from './token';

@makeDraggable
export default class UnitToken extends Token {
    static propTypes = Object.assign({}, Token.propTypes, {
        description: RPropTypes.string,
        fields: RPropTypes.arrayOf(
            RPropTypes.shape({
                choices: RPropTypes.array,
                help_text: RPropTypes.string,
                is_numeric: RPropTypes.bool,
                label: RPropTypes.string,
                required: RPropTypes.bool,
                ui_element: RPropTypes.string,
            }),
        ),
        index: RPropTypes.number,
        onChange: RPropTypes.func,
        onSearch: RPropTypes.func,
        searchKey: RPropTypes.string,
        values: RPropTypes.array,
    });

    constructor(props) {
        super(props);

        this.state = {values: null, triggerSearch: false};
        this.firstField = null;
        this.grabFocus = null;
    }

    componentWillMount() {
        super.componentWillMount();

        this.updateState(this.props.values);
    }

    componentDidMount() {
        if (this.grabFocus === null) {
            this.grabFocus = true;
        }
    }

    componentDidUpdate(newProps) {
        if (this.firstField && this.grabFocus) {
            const node = ReactDOM.findDOMNode(this.firstField.input);
            setTimeout(() => node.focus(), 250);
            this.firstField = null;
            this.grabFocus = false;
        }

        if (!_.isEqual(newProps.values, this.props.values)) {
            this.updateState(this.props.values);
        }

        if (this.state.triggerSearch) {
            this.setState({triggerSearch: false});
            this.props.onSearch();
        }
    }

    updateState(values) {
        if (!_.isEqual(values, this.state.values)) {
            this.setState({values});
        }
    }

    setIndexState(index, value) {
        const values = I.fromJS(this.state.values);

        this.updateState(values.set(index, value).toArray());
    }

    updateGlobalState(fieldIndex, value) {
        const payload = {tokenIndex: this.props.index, fieldIndex, value};

        this.props.onChange(payload);
    }

    get fieldsValues() {
        return _.zip(this.props.fields, this.state.values);
    }

    handleFieldBlur = index => () => {
        this.updateGlobalState(index, this.state.values[index]);
    }

    handleFieldKeyDown = index => (ev) => {
        switch (ev.which) {
            case 13: // Enter
                this.handleFieldEnterKeyDown(index);
                break;
        }

    }

    handleFieldEnterKeyDown = index => {
        this.updateGlobalState(index, this.state.values[index]);

        this.setState({triggerSearch: true});
    }

    handleFieldChange = index => ev => {
        const value = ev.target.value;

        this.setIndexState(index, value);
    };

    handleSelectChange = index => (_, __, value) => {
        this.setIndexState(index, value);

        this.updateGlobalState(index, value);
    }

    handleDateAccept = index => date => {
        date = new Intl.DateTimeFormat("pt-BR").format(date);

        this.setIndexState(index, date);

        this.updateGlobalState(index, date);
    }

    firstFieldRef = index => c => {
        if (index == 0) this.firstField = c;
    }

    makeField = hideLabel => {
        return ([field, value], i) => {
            let input = null;

            let insideStyle = {
                color: this.style.color,
                top: "-10px",
                height: "auto",
                lineHeight: "normal",
                userSelect: "all",
            };

            let outsideStyle = {
                display: "inline-block",
                fontSize: 14,
                margin: 0,
                height: "auto",
                top: "10px",
            };

            switch (field.ui_element) {
                case "SelectField":
                    input = (
                        <SelectField
                            autoWidth
                            iconStyle={{top: -14}}
                            key={`field_${i}_${this.props.index}`}
                            labelStyle={insideStyle}
                            onChange={this.handleSelectChange(i)}
                            style={outsideStyle}
                            value={`${value}`}
                        >
                            {field.choices.map(([choice, text]) => (
                                <MenuItem
                                    key={`${choice}`}
                                    primaryText={text}
                                    value={`${choice}`}
                                />
                            ))}
                        </SelectField>
                    );
                    break;

                case "DatePicker":
                    input = (
                        <div
                            style={{display: "inline-block"}}
                        >
                            <TextField
                                hintText={field.help_text}
                                inputStyle={insideStyle}
                                key={`field_${i}_${this.props.index}`}
                                name={`input_field_${i}_${this.props.index}`}
                                onBlur={this.handleFieldBlur(i)}
                                onChange={this.handleFieldChange(i)}
                                onKeyDown={this.handleFieldKeyDown(i)}
                                ref={this.firstFieldRef(i)}
                                style={{...outsideStyle, width: 210}}
                                value={value}
                            />
                            {this.makeIconButton(ActionDateRange, {
                                iconStyle: {
                                    width: 24,
                                    height: 24,
                                },
                                props: {
                                    onClick: () => {
                                        this.datePickers[i].show();
                                    },
                                },
                            })}
                            <DatePickerDialog
                                DateTimeFormat={Intl.DateTimeFormat}
                                autoOk
                                firstDayOfWeek={0}
                                locale="pt-BR"
                                maxDate={new Date()}
                                onAccept={this.handleDateAccept(i)}
                                ref={c => this.datePickers[i] = c}
                            />
                        </div>
                    );
                    break;

                default:
                    input = (
                        <TextField
                            hintText={field.help_text}
                            inputStyle={insideStyle}
                            key={`field_${i}_${this.props.index}`}
                            name={`input_field_${i}_${this.props.index}`}
                            onBlur={this.handleFieldBlur(i)}
                            onChange={this.handleFieldChange(i)}
                            onKeyDown={this.handleFieldKeyDown(i)}
                            ref={this.firstFieldRef(i)}
                            style={{...outsideStyle, width: "auto"}}
                            value={value}
                        />
                    );
            }

            return (
                <div key={i}>
                    {!hideLabel &&
                        <div
                            style={{
                                display: "inline-block",
                                margin: "0 6px",
                            }}
                        >
                            {field.label}
                        </div>
                    }
                    {input}
                </div>
            );
        };
    }

    renderContents() {
        const hideLabel = this.props.fields.length == 1;
        let description = (hideLabel) ?
            this.props.fields[0].label :
            this.props.description;

        this.datePickers = {};

        return (
            <div
                style={{
                    display: "inline-flex",
                    flexFlow: "row no-wrap",
                    justifyContent: "flex-start",
                }}
            >
                <p
                    style={{
                        marginRight: "12px",
                        ...this.uppercaseStyle,
                    }}
                >
                    {description}
                </p>
                {this.fieldsValues.filter(([f]) => f)
                    .map(this.makeField(hideLabel))}
            </div>
        );

    }
}

