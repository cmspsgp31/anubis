define [ "backbone"
	, "underscore"
	, "jquery"
	, "swig"
	, "anubis/views"
	, "anubis/delegates"
	],
(Backbone, _, $, swig, Views, Delegates) ->
	exports = {}

	exports.BooleanTokenDelegate = class BooleanTokenDelegate extends Delegates.Delegate
		constructor: ->
			super
			@el.sortable
				containment: "parent"
				# axis: "x"

		createEditor: ->
			@editor = $ """
			<li data-token="editor">
			<fieldset>
			<p><input type="text" /></p>
			</fieldset>
			</li>
			"""

			@el.append @editor

			@input = $ "input", @editor

			@makeInputAutocompletable()

			@input.focus()

		makeInputAutocompletable: ->
			@input.autocomplete
				source: @view.autocompleteFilters()
				minLength: 0
				select: (ev, ui) =>
					@input.val ui.item.value
					@view.handleExpression ev


		inputVal: -> @input.val()

		clearInput: -> @input.val("")

		moveEditorTo: (anchor, after=true) ->
			method = if after then "insertAfter" else "insertBefore"

			@editor.remove()
			@editor[method] anchor
			@makeInputAutocompletable()
			@input.focus()

		moveEditorLeft: ->
			prev = @editor.prev()

			if prev.length > 0 then @moveEditorTo prev, false

		moveEditorRight: ->
			next = @editor.next()

			if next.length > 0 then @moveEditorTo next

		error: -> @el.effect
			effect: "pulsate"
			duration: "slow"
			times: 3

		makeToken: (tokenType, tokenName, filter) ->
			if filter?
				if filter.arg_count == 1
					legend = " style=\"display: none;\""
				else
					legend = ""
				contents = """
				<fieldset>
				<div class="legend"#{legend}>#{filter.description}</div>
				#{filter.template}
				</fieldset>
				"""
			else
				contents = "<p></p>"

			if tokenName?
				tokenName = " data-name=\"#{tokenName}\""
			else
				tokenName = ""

			newToken = $ """
				<li data-token="#{tokenType}"#{tokenName}>
				#{contents}
				</li>
			"""

			newToken

		findToken: (source) ->
			sources = ($ el for el in source.parents())
			sources.unshift $ source

			for el in sources
				if (el.data "token")?
					token = el
					break

			token

		insertToken: (token) ->
			token.hide()
			token.insertBefore @editor

			token.show
				effect: "puff"
				duration: 150
				complete: ->
					firstInput = $ "p:first-of-type > :focusable", token
					if firstInput.size() then firstInput.focus()


		removeToken: (token) ->
			effect = token.effect
				effect: "puff"
				duration: 150

			effect.promise().then -> token.remove()

		removePreviousToken: ->
			previous = @editor.prev()

			if previous.length > 0 then @removeToken previous

		setTokenData: (token, data) ->
			for [el, datum] in _.zip ($ "input, select, textarea", token), data
				($ el).val datum



	exports.BooleanTokenView = class BooleanTokenView extends Views.RouteableView
		@delegate: BooleanTokenDelegate
		@tokenTypes:
			[ "expression"
			, "and"
			, "or"
			, "negate"
			, "open"
			, "close"
			]

		@tokenExpressions:
			"or": "Ou, ou (operador)"
			"and": "E, e (operador)"
			"negate": "Não, Exceto (operador)"

		constructor: ->
			super
			@tokenCache = {}

			@delegate.createEditor()

		translator: -> (@getData "translator").replace /\/$/, ""

		activate: (expression) ->
			(@translationPromise expression).done (obj) =>
				@tokenCache[expression] = obj["expression"]
				@delegate.update obj["expression"]
				@delegate.createEditor()

		translationPromise: (expression) ->
			if expression not in _.keys @tokenCache
				defer = $.ajax
					type: "GET"
					dataType: "json"
					url: "#{@translator()}/#{expression}"
			else
				defer = new $.Deferred
				defer.resolve expression: @tokenCache[expression]

			defer

		filters: -> @constructor.templates.get(@getData "filters")

		tokens: -> @delegate.select "li[data-token]"

		autocompleteFilters: ->
			filters = []

			for name, data of @filters()
				filters.push
					value: name
					label: data.description

			filters = _.sortBy filters, (filter) -> filter.label

			for name, data of @constructor.tokenExpressions
				filters.unshift
					value: name
					label: data

			filters

		events:
			"keydown [data-token='editor'] input": "dynamicInputKeydown"
			"click": "fieldClick"

		fieldClick: (ev) ->
			target = $ ev.target
			token = @delegate.findToken target
			if not token?
				ev.preventDefault()
				@delegate.input.focus()
			else if (token.data "token") == "editor"
				@delegate.input.autocomplete "search", ""
			else if ev.which == 2
				ev.preventDefault()
				ev.stopPropagation()
				@delegate.removeToken token
				@delegate.input.focus()

		dynamicInputKeydown: (ev) ->
			if (ev.which >= 65) and (ev.which <= 90)
				# letters
				@handleIgnore(ev)
			else if (ev.which >= 96) and (ev.which <= 105)
				# numpad numbers
				@handleIgnore(ev)
			else if (ev.which >= 50) and (ev.which <= 54)
				# top row numbers
				@handleIgnore(ev)
			else
				switch ev.which
					# backspace
					when 8 then @handleBackspace(ev)
					# modifiers, arrows, delete, underscore and hyphen
					when 16, 17, 18, 20, 38, 46, 189, 40
						@handleIgnore(ev)
					# down arrow
					# when 40 then @handleTrigger(ev)
					# numpad star, both forward slashes
					when 191, 111, 106 then @handleAnd(ev)
					# numpad plus
					when 107 then @handleOr(ev)
					# enter
					when 13 then @handleSubmit(ev)
					# space
					when 32 then @handleDefaultExpression(ev)
					# esc
					when 27 then @handleClear(ev)
					# caret, inactive due to trouble with dead keys
					# when 229 then @handleNot(ev)
					# left, right
					when 37, 39
						if @delegate.inputVal() == ""
							@handleEditorMovement(ev)
						else
							@handleIgnore(ev)
					# bang
					when 49
						if ev.shiftKey
							@handleNot(ev)
						else
							@handleIgnore(ev)
					# tab
					when 9
						if ev.shiftKey
							@handleIgnore(ev)
						else
							@handleExpression(ev)
					# shift equal, shift backslash
					when 187, 220
						if ev.shiftKey
							@handleOr(ev)
						else
							@handleDefaultExpression(ev)
					# shift seven, shift eight
					when 55, 56
						if ev.shiftKey
							@handleAnd(ev)
						else
							@handleIgnore(ev)
					# shift nine
					when 57
						if ev.shiftKey
							@handleOpen(ev)
						else
							@handleIgnore(ev)
					# shift zero
					when 48
						if ev.shiftKey
							@handleClose(ev)
						else
							@handleIgnore(ev)
					else @handleDefaultExpression(ev)

		handleEditorMovement: (ev) ->
			if ev.which == 37
				@delegate.moveEditorLeft()
			else
				@delegate.moveEditorRight()

		handleSubmit: (ev) ->
			tokens = @tokens()

			if @delegate.inputVal() != ""
				@insertTokenWithData (@getData "default"),
					[@delegate.inputVal()]


		handleClear: (ev) -> @delegate.clearInput()

		handleDefaultExpression: (ev) ->
			@insertTokenWithData (@getData "default"), [@delegate.inputVal()]

		handleIgnore: (ev) ->

		handleBackspace: (ev) ->
			if @delegate.inputVal().length == 0
				@delegate.removePreviousToken()

		handleExpression: (ev) ->
			ev.preventDefault()
			if ev.type == "autocompleteselect" then ev.stopPropagation()

			name = @delegate.inputVal()
			filters = @filters()

			if name in _.keys filters
				@insertToken "expression", name, filters[name]
			else if name in @constructor.tokenTypes
				@insertToken name
			else
				@delegate.error()

		handleOr: (ev) ->
			ev.preventDefault()
			@insertToken "or"

		handleAnd: (ev) ->
			ev.preventDefault()
			@insertToken "and"

		handleOpen: (ev) ->
			ev.preventDefault()
			@insertToken "open"

		handleNot: (ev) ->
			ev.preventDefault()
			@insertToken "negate"

		handleClose: (ev) ->
			ev.preventDefault()
			@insertToken "close"

		insertToken: (tokenType, tokenName, filter) ->
			token = @delegate.makeToken tokenType, tokenName, filter

			@delegate.insertToken token

			@handleClear()

			token

		insertTokenWithData: (tokenName, data) ->
			filter = @filters()[tokenName]
			token = @insertToken "expression", tokenName, filter

			@delegate.setTokenData token, data


		serialize: ->
			expression = ""

			for token in @tokens()
				token = $ token
				if (token.data "token") == "editor" then continue

				switch token.data "token"
					when "and" then expression += "/"
					when "negate" then expression += "!"
					when "or" then expression += "+"
					when "open" then expression += "("
					when "close" then expression += ")"
					else
						identifier = token.data "name"
						args = []

						for elem in ($ "input, textarea, select", token)
							arg = ($ elem).val().replace(/\$/, "$$") \
							.replace(/"/, "$\"")
							arg = "\"#{arg}\""
							args.push arg

						expression += "#{identifier}," + args.join()

			obj = {}
			obj[@getData "name"] = "(#{expression})"

			obj

	exports
