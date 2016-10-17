// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// token_selector.js - floating action button component for the interface.

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
import _ from 'lodash';
import {FloatingActionButton} from 'material-ui';
import {TransitionMotion, spring} from 'react-motion';

import {
    ActionSearch,
    NavigationClose,
    ContentAdd,
} from 'material-ui/svg-icons';

import {PropTypes as RPropTypes} from 'react';

export default class TokenSelector extends React.Component {
    static propTypes = {
        onSearch: RPropTypes.func.isRequired,
        style: RPropTypes.object,
    }

    constructor(props) {
        super(props);

        this.state = {
            isTouching: false,
            expandFAB: false,
            endTouchAction: null,
        };
    }

    baseStyle = {
        position: "fixed",
        display: "flex",
        flexFlow: "column-reverse nowrap",
        alignItems: "center",
        alignContent: "center",
        justifyContent: "flex-start",
        bottom: "80px",
        right: "24px",
        zIndex: 9000,
    }

    itemStyle = {
        marginTop: "12px",
        marginLeft: 0,
        marginRight: 0,
        marginBottom: 0,
    }

    get style() {
        return Object.assign({}, this.baseStyle, this.props.style);
    }

    handleExpand = () => {
        if (this.state.isTouching) {
            this.setState({expandFAB: true});
        }
    }

    handleContract = () => {
        if (this.state.expandFAB) {
            this.setState({expandFAB: false});
        }
    }

    handleStartTouch = () => {
        this.setState({isTouching: true});

        if (this.state.expandFAB) {
            this.setState({endTouchAction: this.handleContract});
        }
        else {
            this.setState({endTouchAction: ev => {
                if (!this.state.expandFAB) {
                    this.props.onSearch(ev);
                }
            }});

            setTimeout(this.handleExpand, 500);
        }
    }

    handleEndTouch = () => {
        this.setState({isTouching: false});

        if (this.state.endTouchAction) {
            this.state.endTouchAction();
            this.setState({endTouchAction: null});
        }
    }

    handleClick = ev => {
        this.props.onSearch(ev);
    }


    renderFAB() {
        const isExpanded = this.state.expandFAB;
        const icon = (isExpanded) ?
            key => <NavigationClose key={key} /> :
            key => <ActionSearch key={key} />;

        const config = {
            rotation: {
                precision: 3.6,
            },
            opacity: {
                precision: 1,
            },
        };

        const style = {
            key: (isExpanded) ? "close" : "search",
            data: icon,
            style: {
                rotate: spring((isExpanded) ? 360 : 0, config.rotation),
                opacity: spring(100, config.opacity),
            },
        };

        return (
            <TransitionMotion
                styles={[style]}
                willEnter={() => ({
                    rotate: (isExpanded) ? 0 : 360,
                    opacity: 0,
                })}
                willLeave={() => ({
                    rotate: spring((isExpanded) ? 0 : 360, config.rotation),
                    opacity: spring(0, config.opacity),
                })}
            >
                {s =>
                    <div style={this.itemStyle}>
                        {s.map(this._makeFAB)}
                    </div>
                }
            </TransitionMotion>
        );
    }

    _makeFAB = (conf, i) => {
        let children = conf.data(conf.key);

        let style = {
            transform: `rotate(${conf.style.rotate}deg)`,
            opacity: conf.style.opacity/100,
            display: "inline-block",
            marginLeft: (i > 0) ? "-56px" : 0,
            zIndex: (i > 0) ? 9003 : 9002,
            position: "relative",
        };

        return (
            <div style={style}>
                <FloatingActionButton
                    onMouseDown={this.handleStartTouch}
                    onMouseUp={this.handleEndTouch}
                    onTouchEnd={this.handleEndTouch}
                    onTouchStart={this.handleStartTouch}
                >
                    {children}
                </FloatingActionButton>
            </div>
        );
    }

    renderExpandable() {
        /*eslint-disable react/jsx-key*/
        let icons = [
            ['add_button', <ContentAdd />],
            ['search_button', <ActionSearch />],
        ];
        /*eslint-enable react/jsx-key*/

        const keys = icons.map(([key, __unused]) => key);

        icons = _.fromPairs(icons);

        let styles = (this.state.expandFAB) ? keys.map(key => ({
            key,
            style: { offset: spring(0, {precision: 0.6}) },
        })) : [];

        return (
            <TransitionMotion
                styles={styles}
                willEnter={() => ({offset: 60})}
                willLeave={() => ({offset: spring(60, {precision: 0.6})})}
            >
                {styles =>
                    <div style={this.style}>
                        {this.renderFAB()}

                        {styles.map(({key, style: s}) => {
                            let icon = icons[key];
                            let style = {
                                ...this.itemStyle,
                                marginBottom: `-${s.offset}px`,
                                zIndex: 9001,
                                position: "relative",
                            };

                            return (
                                <div
                                    key={key}
                                    style={style}
                                >
                                    <FloatingActionButton
                                        mini
                                        secondary
                                    >
                                        {icon}
                                    </FloatingActionButton>
                                </div>
                            );
                        })}
                    </div>
                }
            </TransitionMotion>
        );
    }

    render() {
        return (
            <div style={this.style}>
                <FloatingActionButton onTouchTap={this.handleClick}>
                    <ActionSearch />
                </FloatingActionButton>
            </div>
        );
    }
}
