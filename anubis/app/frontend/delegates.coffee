define ["jquery", "underscore", "ui"], ($, _, ui) ->
	class Delegate
		constructor: (@el, @view) ->
			@el.data "viewObject", @view

			@waitEl = @select "> [data-wait]"

			if @waitEl.length == 0
				@waitEl = $ "<h1>AGUARDE...</h1>"
			else
				@waitEl.remove()

			@waiting = null
			@updating = null

		@forElement: (el) ->
			el = $ el
			if (el.data "viewObject")?
				(el.data "viewObject").delegate
			else
				null

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

		update: (contents) ->
			if not @updating
				@updating = new $.Deferred

				if @waiting?
					@waiting.then => @updating.resolve()
				else
					@updating.resolve()

			updating = @updating

			updating.then =>
				@el.html contents
				@bindEvents()
				@updating = null

			updating

		wait: ->
			if not @waiting?
				@waiting = new $.Deferred

				if (($ 'body').has @waitEl).length == 0
					@waitEl.insertAfter @el
					@waiting.then => @waitEl.remove()

				@enterWaitMode()

			@waiting

		stopWaiting: ->
			if @waiting?
				@exitWaitMode()

				@waiting.resolve()
				@waiting = null

		enterWaitMode: ->
			@el.hide()
			@waitEl.show()

		exitWaitMode: ->
			@waitEl.hide()
			@el.show()


	class ActiveOnShowDelegate extends Delegate
		show: -> @setActive true
		hide: -> @setActive false

	class SearchTypeDelegate extends Delegate
		hide: -> @el.slideUp(200)
		show: -> @el.slideDown(200)

	class ModalDelegate extends Delegate
		constructor: ->
			super
			@shouldHide = false
			@el.addClass("modal").addClass "fade"

			@el.on "hide.bs.modal", (ev) =>
				if not @shouldHide
					ev.preventDefault()
					(@select "[data-close]").trigger "click"

				@shouldHide

			@el.on "hidden.bs.modal", => @shouldHide = false

		bindEvents: ->
			(@select "[data-close]").on "click", (ev) =>
				@view.router.navigate @view.router.lastNonModalMatch,
					trigger: true

		show: -> @el.modal("show")

		hide: ->
			@shouldHide = true
			@el.modal("hide")

	class FormDelegate extends Delegate
		filter: ":input:visible, [data-form-control]:visible, :visible > input[type=hidden]"

		findSerializer: (element) ->
			element = $ element

			if (element.is "[data-form-control]")
				return "serializeFormControl"
			else if (element.is "[data-form-control] *")
				return "serializeSkip"
			# else if (element.is "input[type=radio]")
			else
				return "serializeJQuery"

		serializeJQuery: (elements) ->
			array = ($ elements).serializeArray()
			obj = {}

			for field in array
				if not (field.name in _.keys(obj))
					obj[field.name] = @format field.value
				else
					if not (_.isArray obj[field.name])
						obj[field.name] = [obj[field.name]]

					obj[field.name].push @format field.value

			obj

		serializeSkip: -> {}

		serializeFormControl: (elements) ->
			obj = {}

			for element in elements
				view = ($ element).data "viewObject"
				_.extend obj, view.serialize()

			obj

		serialize: ->
			controls = _.groupBy (@select @filter), @findSerializer
			obj = {}

			for serializer, elements of controls
				serializer = $.proxy @[serializer], @
				_.extend obj, serializer elements

			obj

		format: (value) -> (encodeURIComponent value).replace /%2F/ig, "/"

		value: (key) ->
			el = @select "[name='#{key}']"

			if not el.length then null else el.val()

	class CollectionDelegate extends Delegate
		constructor: ->
			super

			@notFoundEl = @select "> [data-not-found]"

			if @notFoundEl.length == 0
				@notFoundEl = $ "<div><h1>NÃO ENCONTRADO</h1></div>"

			@notFoundEl.hide()

			@advancing = null

			if @el.is "[data-paginate]"
				@paginationTrigger = @select "[data-next-page]"
				($ window).scroll (ev) => @checkPaginate ev
				($ window).resize (ev) => @checkPaginate ev

		checkPaginate: (ev) ->
			rect = @paginationTrigger[0].getBoundingClientRect()

			if rect.bottom < ($ window).height() and not @advancing?
				@advancing = @view.gotoNextPage()
				@advancing.then => @advancing = null

		updateCurrentPage: (page) ->
			(@select "[data-current-page-display]").html page

		updateTotalPages: (totalPages) ->
			(@select "[data-total-pages-display]").html totalPages

		found: -> @notFoundEl.hide()
		notFound: -> @notFoundEl.show()



	Delegate: Delegate
	SearchTypeDelegate: SearchTypeDelegate
	ModalDelegate: ModalDelegate
	FormDelegate: FormDelegate
	ActiveOnShowDelegate: ActiveOnShowDelegate
	CollectionDelegate: CollectionDelegate
