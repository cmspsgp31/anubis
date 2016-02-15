export let Editor = {
	ReducerMap: {
		'ENABLE_EDITOR': state => state.set('canSearch', true),
		'DISABLE_EDITOR': state => state.set('canSearch', false),
		'TOGGLE_EDITOR': state => state.update('canSearch', v => !v),
	},
	keyPath: ['tokenEditor'],
}

