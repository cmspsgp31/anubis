define ['underscore', 'jquery', 'backbone'], (_, $, Backbone) ->
	_sync = Backbone.sync

	Backbone.sync = (method, model, options) ->
		usrBeforeSend = if options? and "beforeSend" of options then options.beforeSend else ->
		if not options? then options = {}
		
		options.beforeSend = (xhr) ->
			token = $('meta[name="csrf-token"]').attr "content"
			xhr.setRequestHeader "X-CSRFToken", token

			usrBeforeSend xhr

		return _sync method, model, options

	return Backbone




