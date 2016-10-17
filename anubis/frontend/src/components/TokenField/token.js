// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// token.js - token base class.

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
import IPropTypes from 'react-immutable-proptypes';

import {PropTypes as RPropTypes} from 'react';
import {Paper} from 'material-ui';
import {IconButton} from 'material-ui';
import {ContentClear} from 'material-ui/svg-icons';
import {DragSource, DropTarget} from 'react-dnd';

const tokenSource = {
    beginDrag(props) {
        return props.token;
    },
};

export const tokenTarget = (getIndex) => ({
    canDrop() {
        return false;
    },

    hover(props, monitor, component) {
        const draggedToken = monitor.getItem().get('index');
        const overToken = getIndex(props);

        const offset = monitor.getClientOffset();
        const rect = ReactDOM.findDOMNode(component).getBoundingClientRect();

        const diffLeft = Math.abs(rect.left - offset.x);
        const diffRight = Math.abs(rect.right - offset.x);

        let overOffset = 0;

        if (diffLeft > diffRight) overOffset = 1;

        props.onSort(draggedToken, overToken, overOffset);
    },
});

export const TokenType = "__TOKEN__";

export const makeDraggable = subcls => {
    const makeSource = DragSource(TokenType, tokenSource, (c, m) => ({
        dragSource: c.dragSource(),
        isDragging: m.isDragging(),
    }));

    const boundTokenTarget = tokenTarget(props => props.token.get('index'));

    const makeTarget = DropTarget(TokenType, boundTokenTarget, c => ({
        dropTarget: c.dropTarget(),
    }));

    return makeTarget(makeSource(subcls));
};

export default class Token extends React.Component {
    static propTypes = {
        dragSource: RPropTypes.func,
        dropTarget: RPropTypes.func,
        index: RPropTypes.number,
        isDragging: RPropTypes.bool,
        onRemove: RPropTypes.func,
        onSort: RPropTypes.func,
        setEditorValue: RPropTypes.func,
        style: RPropTypes.object,
        textElement: RPropTypes.func,
        token: IPropTypes.contains({
            key: RPropTypes.string.isRequired,
            index: RPropTypes.number.isRequired,
            args: IPropTypes.listOf(RPropTypes.string),
        }),
    }

    static contextTypes = {
        muiTheme: RPropTypes.object,
    }

    componentWillMount() {
        this.props.setEditorValue("");
    }

    get baseStyle() {
        const bgColor = this.context.muiTheme.rawTheme.palette.primary2Color;
        const textBgColor = this.context.muiTheme.rawTheme.palette.
            alternateTextColor;

        return {
            fontSize: 14,
            padding: '8px',
            marginRight: '10px',
            marginBottom: '12px',
            backgroundColor: bgColor,
            color: textBgColor,
            position: 'relative',
            cursor: 'move',
            userSelect: 'none',
        };
    }

    get style() {
        return Object.assign({}, this.baseStyle, this.props.style, {
            opacity: (this.props.isDragging) ? 0.5 : 1,
        });
    }

    baseIconButtonStyle = {
        position: "relative",
        display: "inline-block",
        height: 24,
        width: 24,
        padding: 0,
        verticalAlign: "middle",
        marginLeft: 12,
    }

    baseIconButtonIconStyle = {
        height: 18,
        width: 18,
        verticalAlign: "middle",
    }

    uppercaseStyle = {
        fontWeight: 500,
        textTransform: 'uppercase',
    };

    makeIconButton(icon, options={style: {}, iconStyle: {}, props: {},
                   iconProps: {}}) {
        const style = Object.assign({}, this.baseIconButtonStyle,
                                    options.style);

        const iconStyle = Object.assign({}, this.baseIconButtonIconStyle,
            options.iconStyle);

        const props = Object.assign({}, {
            tabIndex: -1,
            iconStyle,
            style,
        }, options.props);

        const iconProps = Object.assign({}, {
            style: iconStyle,
            color: this.style.color,
        }, options.iconProps);

        return React.createElement(IconButton, props, [
            React.createElement(icon, iconProps),
        ]);
    }

    renderCloseButton(style = {}, iconStyle = {}) {
        return this.makeIconButton(ContentClear, {
            style,
            iconStyle,
            props: {
                key: "__CLOSE_BUTTON__",
                onClick: () => this.props.onRemove(this.props.index),
            },
        });
    }

    renderContents() {
        return "";
    }

    render() {
        let contents = React.cloneElement(this.renderContents(),
            {key: "__TOKEN_CONTENT__"});

        contents = [contents, this.renderCloseButton()];

        return this.props.dragSource(this.props.dropTarget(
            <div>
                <Paper
                    ref={c => this.element = c}
                    style={this.style}
                    zDepth={1}
                >
                    {contents}
                </Paper>
            </div>
        ));
    }

}
