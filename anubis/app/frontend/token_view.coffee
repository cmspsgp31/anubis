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
			@el.sortable containment: "parent"

		createEditor: (options=focus: false) ->
			{focus} = options

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

			if focus then @input.focus()

		makeInputAutocompletable: ->
			@input.autocomplete
				source: @view.autocompleteFilters()
				minLength: 0
				select: (ev, ui) =>
					if ui.item.value in _.keys BooleanTokenView.tokenExpressions
						@view.handleDefaultExpression()

					@input.val ui.item.value
					token = @view.handleExpression ev

					if (token.data "token") != "expression"
						@input.focus()


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
				<button type="button" class="close" tabindex="-1" data-remove>&times;</button>
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
			"close": ") (fecha parênteses)"
			"open": "( (abre parênteses)"
			"or": "Ou, ou (operador)"
			"and": "E, e (operador)"
			"negate": "Não (operador)"

		constructor: ->
			super
			@listenAll()

			@tokenCache = {}

			@delegate.createEditor focus: true

		listenAll: ->
			id = @$el.attr "id"
			($ "[data-token-clear=#{id}]").on "click", => @clearAllTokens()
			($ "[data-token-show-list=#{id}]").on "click", => @showTokenList()
			($ "[data-token-insert=#{id}]").on "click", (ev) =>
				target = $ ev.target

				tokens = @tokens()
				if (tokens.length > 1)
					lastToken = $ @delegate.editor.prev()
					if (lastToken.data "token") in ["expression", "close"]
						@insertToken "and"

				@insertTokenWithData (target.data "tokenName"),
					[target.data "tokenValue"]

		clearAllTokens: (ev) ->
			@delegate.update ""
			@delegate.createEditor focus: true

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

		filters: -> @constructor.templates.get (@getData "tokenList")

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
			"click [data-remove]": "removeClick"
			"click": "fieldClick"

		fieldClick: (ev) ->
			target = $ ev.target
			token = @delegate.findToken target
			if not token?
				ev.preventDefault()
				@delegate.input.focus()

		removeClick: (ev) ->
			token = @delegate.findToken ($ ev.target)

			if token? then @delegate.removeToken token

		showTokenList: -> @delegate.input.autocomplete "search", ""

		dynamicInputKeydown: (ev) ->
			switch ev.which
				# backspace
				when 8 then @handleBackspace(ev)
				# down arrow
				# when 40 then @handleTrigger(ev)
				# numpad star, both forward slashes
				when 191, 111, 106 then @handleAnd(ev)
				# numpad plus
				when 107 then @handleOr(ev)
				# enter
				# when 13 then @handleIgnore(ev)
				# space
				# when 32 then @handleDefaultExpression(ev)
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
						@handleIgnore(ev)
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
				else @handleIgnore(ev)

		handleEditorMovement: (ev) ->
			if ev.which == 37
				@delegate.moveEditorLeft()
			else
				@delegate.moveEditorRight()

		handleClear: (ev) -> @delegate.clearInput()

		handleDefaultExpression: (ev) ->
			inputContents = @delegate.inputVal()
			if inputContents != ""
				@insertTokenWithData (@getData "default"), [inputContents]

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

		handleNonExpressionToken: (ev, tokenName) ->
			ev.preventDefault()
			@handleDefaultExpression ev
			@insertToken tokenName
			@delegate.input.focus()

		handleOr: (ev) -> @handleNonExpressionToken ev, "or"

		handleAnd: (ev) -> @handleNonExpressionToken ev, "and"

		handleNot: (ev) -> @handleNonExpressionToken ev, "negate"

		handleOpen: (ev) -> @handleNonExpressionToken ev, "open"

		handleClose: (ev) -> @handleNonExpressionToken ev, "close"

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
			@handleDefaultExpression()

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
			obj[@getData "name"] = expression

			obj

	exports
