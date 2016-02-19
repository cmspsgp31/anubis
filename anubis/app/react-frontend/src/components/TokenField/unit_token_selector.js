/* eslint-disable react/no-set-state */

import React from 'react';
import {FloatingActionButton} from 'material-ui';
import {TransitionMotion, spring} from 'react-motion';

import {
	ActionSearch,
	NavigationClose,
	ContentAdd,
} from 'material-ui/lib/svg-icons';

import {PropTypes as RPropTypes} from 'react';

export default class UnitTokenSelector extends React.Component {
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
		margin: "12px 0 0 0",
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

	submenuItems() {
		let items = [
			<FloatingActionButton
				key="add_button"
				mini
				secondary
				style={this.itemStyle}
			>
				<ContentAdd />
			</FloatingActionButton>,
			<FloatingActionButton
				key="search_button"
				mini
				secondary
				style={this.itemStyle}
			>
				<ActionSearch />
			</FloatingActionButton>,
		];

		return items;
	}

	renderFAB() {
		let isExpanded = this.state.expandFAB;
		let icon = (isExpanded) ?
			key => <NavigationClose key={key} /> :
			key => <ActionSearch key={key} />;

		let config = {
			rotation: {
				precision: 3.6,
			},
			opacity: {
				precision: 1,
			},
		};

		let style = {
			key: (isExpanded) ? "close" : "search",
			data: icon,
			style: {
				rotate: spring(0, config.rotation),
				opacity: spring(100, config.opacity),
			},
		};

		return (
			<TransitionMotion
				styles={[style]}
				willEnter={() => ({
					rotate: 360,
					opacity: 0,
				})}
				willLeave={() => ({
					rotate: spring(360, config.rotation),
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
			zIndex: (i > 0) ? 9002 : 9001,
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

	render() {
		return (
			<div style={this.style}>
				{this.renderFAB()}

				{this.state.expandFAB && this.submenuItems()}
			</div>
		);
	}
}
