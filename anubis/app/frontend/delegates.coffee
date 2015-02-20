define ["jquery", "underscore", "ui", "swig"], ($, _, ui, swig) ->
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

		enable: -> @el.prop "disabled", false

		disable: -> @el.prop "disabled", true

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

		detach: -> @el.detach()

		remove: -> @el.remove()

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

	class UnroutedModalDelegate extends Delegate
		constructor: ->
			super
			(@el.addClass "modal").addClass "fade"
			@visible = false
			@shouldHide = false

			@el.on "hide.bs.modal", (ev) =>
				if not @shouldHide
					ev.preventDefault()
					(@select "[data-close]").trigger "click"

				@shouldHide

			@el.on "hidden.bs.modal", => @shouldHide = false

		bindEvents: ->
			(@select "[data-close]").on "click", => @view.destroy()

		remove: -> @hide().then => @el.remove()

		show: ->
			willShow = new $.Deferred

			@el.one "shown.bs.modal", =>
				@visible = true
				willShow.resolve()

			@el.modal "show"

			willShow

		hide: ->
			@shouldHide = true
			willHide = new $.Deferred

			@el.one "hidden.bs.modal", =>
				@visible = false
				willHide.resolve()

			@el.modal "hide"

			willHide

	class ModalDelegate extends UnroutedModalDelegate
		bindEvents: ->
			(@select "[data-close]").on "click", (ev) =>
				what = @view.router.navigate @view.router.lastNonModalMatch,
					trigger: true


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

		disable: ->
			controls = @select @filter

			for control in controls
				control = $ control
				delegate = Delegate.forElement control

				if delegate? then delegate.disable()
				else control.prop 'disabled', true

		enable: ->
			controls = @select @filter

			for control in controls
				control = $ control
				delegate = Delegate.forElement control

				if delegate? then delegate.enable()
				else control.prop 'disabled', false

	class CollectionDelegate extends Delegate
		constructor: ->
			super

			@notFoundEl = @select "> [data-not-found]"

			if @notFoundEl.length == 0
				@notFoundEl = $ "<div><h1>NÃO ENCONTRADO</h1></div>"

			@notFoundEl.hide()

			@advancing = null

		preparePagination: ->
			@paginationTrigger = @select "[data-next-page]"
			@paginationTrigger.on "click", =>
				if not @advancing?
					@advancing = @view.gotoNextPage()
					@advancing.then => @advancing = null

			# ($ window).scroll (ev) => @checkPaginate ev
			# ($ window).resize (ev) => @checkPaginate ev

		checkPaginate: (ev) ->
			rect = @paginationTrigger[0].getBoundingClientRect()

			if rect.bottom < ($ window).height() and not @advancing?
				@advancing = @view.gotoNextPage()
				@advancing.then => @advancing = null

		updateCurrentPage: (page) ->
			(@select "[data-current-page-display]").html page

		updateTotalPages: (totalPages) ->
			(@select "[data-total-pages-display]").html totalPages
		
		updateTotalObjects: (totalObjects) ->
			if (parseInt totalObjects) != 0
				(@select "[data-results-display]").show()
				(@select "[data-empty-display]").hide()
				(@select "[data-total-objects-display]").html totalObjects
			else
				(@select "[data-results-display]").hide()
				(@select "[data-empty-display]").show()
		
		updateShowing: (recordCount) ->
			(@select "[data-showing]").html recordCount
		
		anchorForPage: (page) ->
			"""
			<div class="clearfix"></div>
			<a name='page-#{page}' data-page='#{page}'></a>
			"""

		linkForPage: (page) ->
			recordNumber = ((parseInt page) - 1) * @view.objectsPerPage + 1
			"<li><a href='#' data-goto-page='#{page}'>#{recordNumber} em diante</a><li>"

		linkForNext: ->
			"<li><a href='#' data-show-all>Carregar todos</a></li>"

		createPageLinks: ->
			menu = @select "[data-page-list]"
			($ "*", menu).off()

			contents = (@linkForPage ($ pageElem).data "page" \
				for pageElem in @select "[data-page]")

			if @view.hasNextPage
				contents.push "<li class='divider'></li>"
				contents.push @linkForNext()

			menu.html contents.join ""

			($ "[data-goto-page]", menu).on "click", (ev) =>
				ev.preventDefault()
				page = ($ ev.target).data "gotoPage"
				@moveToPage page

			($ "[data-show-all]", menu).on "click", (ev) =>
				ev.preventDefault()
				@view.gotoLastPage()

		moveToPage: (page) ->
			offset = ($ "[data-page=#{page}]").offset().top
			offset -= ($ "header").height()
			promise = new $.Deferred
			($ "html, body").animate scrollTop: offset,
				duration: 250
				done: -> promise.resolve()
			promise

		found: -> @notFoundEl.hide()
		notFound: -> @notFoundEl.show()

		setActions: (actions) ->
			actionsList = @select "[data-actions-list]"
			actionsToggle = @select "[data-actions-toggle]"

			console.log actionsToggle[0]
			if actions.length > 0
				actionsToggle.show()
			else
				actionsToggle.hide()

			actionsList.each (i, list) =>
				list = $ list
				list.empty()
				html = ""
				templateName = list.data "actionsList"
				template = @view.constructor.templates.get templateName

				for action in actions
					if "style" not in _.keys action
						action["style"] = "default"
					html += swig.render template, locals: action

				list.html html









	Delegate: Delegate
	SearchTypeDelegate: SearchTypeDelegate
	UnroutedModalDelegate: UnroutedModalDelegate
	ModalDelegate: ModalDelegate
	FormDelegate: FormDelegate
	ActiveOnShowDelegate: ActiveOnShowDelegate
	CollectionDelegate: CollectionDelegate
