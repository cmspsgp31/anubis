define ["jquery", "underscore", "ui"], ($, _, ui) ->
	class Delegate
		constructor: (@el, @view) ->
			@deferUpdate = null
			@el.data "viewObject", @view

		setActive: (active) ->
			if active
				@el.addClass "active"
			else
				@el.removeClass "active"

		show: -> @el.show()
		hide: -> @el.hide()
		select: (pattern) ->
			children = $ pattern, @el
			if @el.is pattern then children = children.add @el
			children

		inserted: -> $("html") in @el.parents()
		insert: (where) ->
			if not @inserted()
				if not where?
					where = $ "main"

				where.append(@el)

		pickWith: (ref, pattern, f, g) ->
			for el in @select pattern
				if not (ref.is el) then g $ el

			f ref

		pickCls: (ref, pattern, cls) -> @pickWith ref, pattern,
			((el) -> el.addClass cls), ((el) -> el.removeClass cls)

		bindEvents: ->

		update: (text) ->
			update = new $.Deferred

			if @deferUpdate?
				@deferUpdate.then =>
					@performUpdate text
					update.resolve()
			else
				@performUpdate text
				update.resolve()

			return update

		performUpdate: (text) ->
			@el.html text
			@bindEvents()

		wait: ->
			if not @deferUpdate?
				@deferUpdate = new $.Deferred
				@deferUpdate.then => @exitWaitMode()
				@enterWaitMode()

		enterWaitMode: ->
			@_waitText = @el.html()
			@performUpdate "AGUARDE"

		exitWaitMode: -> @performUpdate @_waitText

		stopWaiting: ->
			if @deferUpdate?
				@deferUpdate.resolve()
				@deferUpdate = null

	class ActiveOnShowDelegate extends Delegate
		show: -> @setActive true
		hide: -> @setActive false

	
	class GroupRouterDelegate extends Delegate
		switcherByURI: (uri) -> @select "[data-router][href='#{uri}']"
		activateSwitcher: (uri) -> (@switcherByURI uri).addClass "active"
		deactivateSwitcher: (uri) -> (@switcherByURI uri).removeClass "active"

	class GroupRouterParentDelegate extends GroupRouterDelegate
		activateSwitcher: (uri) ->
			el = (@switcherByURI uri).parent()
			el.addClass "active"

		deactivateSwitcher: (uri) ->
			el = (@switcherByURI uri).parent()
			el.removeClass "active"


	class SearchTypeDelegate extends Delegate
		hide: -> @el.slideUp(200)
		show: -> @el.slideDown(200)

	class ModalDelegate extends Delegate
		constructor: ->
			super
			@el.addClass("modal").addClass "fade"

		bindEvents: ->
			(@select "[data-close]").on "click", =>
				@view.router.navigate @view.router.lastNonModalMatch, trigger: true
			
		show: -> @el.modal("show")

		hide: -> @el.modal("hide")

	class FormDelegate extends Delegate
		filter: ":not(form):visible"
		serialize: ->
			array = (@select @filter).serializeArray()
			obj = {}

			for field in array
				if not (field.name in _.keys(obj))
					obj[field.name] = @format field.value
				else
					if not (_.isArray obj[field.name])
						obj[field.name] = [obj[field.name]]

					obj[field.name].push @format field.value

			obj

		format: (value) -> (encodeURIComponent value).replace /%2F/ig, "/"

		value: (key) ->
			el = @select "[name='#{key}']"

			if not el.length then null else el.val()

	class BoolenTokenDelegate extends Delegate
		constructor: ->
			super
			@el.sortable
				containment: "parent"
				# axis: "x"

		createEditor: ->
			@editor = $ """
			<li data-token=\"editor\">
			<fieldset>
			<p><input type=\"text\" /></p>
			</fieldset>
			</li>
			"""

			@el.append @editor

			@input = $ "input", @editor

			@input.autocomplete
				source: @view.autocompleteFilters()
				minLength: 0

			@input.focus()

		inputVal: -> @input.val()

		clearInput: -> @input.val("")

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
			el = source
			token = null

			while el.parent()
				if (el.data "token")?
					token = el
					break
				
				el = el.parent()

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

		removeLastToken: ->
			nextToLast = $ "li[data-token]:nth-last-child(2)", @el
			@removeToken nextToLast




	
	Delegate: Delegate
	SearchTypeDelegate: SearchTypeDelegate
	ModalDelegate: ModalDelegate
	FormDelegate: FormDelegate
	ActiveOnShowDelegate: ActiveOnShowDelegate
	BoolenTokenDelegate: BoolenTokenDelegate
