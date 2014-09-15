define ["jquery", "underscore", "ui"], ($, _, ui) ->
	class Delegate
		constructor: (@el, @view) ->
			@deferUpdate = null
			@el.data "viewObject", @view

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

		findSerializer: (element) ->
			element = $ element

			if (element.is "[data-form-control]")
				return "serializeFormControl"
			else if (element.is "[data-form-control] *")
				return "serializeSkip"
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



	Delegate: Delegate
	SearchTypeDelegate: SearchTypeDelegate
	ModalDelegate: ModalDelegate
	FormDelegate: FormDelegate
	ActiveOnShowDelegate: ActiveOnShowDelegate
