define ["backbone", "underscore", "jquery", "swig", "anubis/delegates"], (Backbone, _, $, swig, Delegates) ->
	exports = {}

	exports.TemplateManager = class TemplateManager
		requestedTemplates: []
		templates: {}
		templatesTried: []
		toTry: []
		promise: null

		request: (uri) ->
			if not (uri in @requestedTemplates)
				@requestedTemplates.push uri

		pull: ->
			if not @promise?
				@promise = new $.Deferred()
				@trying = true
				@toTry = _.reject @requestedTemplates, (t) => t in @templatesTried

				for t in @toTry
					defer = (t) => $.get(t).done (j) => @received t, j
					defer t

				@promise
			else
				null

		received: (t, j) ->
			@toTry = _.without @toTry, t
			@templatesTried.push t
			for template_name, template_body of j
				@templates[template_name] =
					template: template_body
					view: null
			# @templates[t.name] =
			# 	template: j
			# 	view: null

			if @toTry.length == 0
				@promise.resolve()
				@promise = null

		get: (t) -> @templates[t].template

		getView: (t) -> @templates[t].view

		setView: (t, v) -> @templates[t].view = v





	exports.View = class View extends Backbone.View
		@delegate: Delegates.Delegate
		@templates: new TemplateManager
		subviews: []

		constructor: (@router, @options) ->
			@_templateMode = false

			if "template" in _.keys(@options)
				@_templateMode = true
				@baseTemplate = @options.template
				@options.el = document.createElement "div"
			else

			if @options.delegateClass?
				@_delegateClass = @options.delegateClass

			super @options

			if not @baseTemplate? then @baseTemplate = @getData "template"

		getData: (key) ->
			if @_templateMode then @options[key] else @$el.data key

		setData: (key, value) ->
			if @_templateMode
				@options[key] = value
			else
				@$el.data key, value

		delegateClass: ->
			if @_delegateClass? then @_delegateClass else @constructor.delegate

		setElement: (element) ->
			super element
			if @delegate then delete @delegate
			@delegate = new (@delegateClass()) @$el, this

		template: ->
			swig.render (@constructor.templates.get @baseTemplate),
				locals: obj: @model.attributes

		render: ->
			if @baseTemplate?
				delete @subviews
				(@delegate.update @template()).then =>
					@subviews = @constructor.scanViews @router, @$el

		@scanViews: (router, parent) ->
			views = []

			for el in $ "[data-view]", parent
				el = $ el
				viewName = el.data "view"
				options = el: el

				if el.data "delegate"
					options.delegateClass = Delegates[el.data "delegate"]

				try
					views.push new exports[viewName] router, options
				catch e
					console.log exports
					console.log viewName
					throw e

			return views


	exports.RouteableView = class RouteableView extends View
		isMatch: false
		active: false
		matchArgs: null
		lastMatchArgs: null

		constructor: (router, options) ->
			super

			if (@getData "active")? then @setActive true

			@autoRoute()

			@router.on "route", (args...) => @routeEvent args

		autoRoute: ->
			if @getData "route"
				route = new RegExp @getData "route"
				@setRoute route
			else if @getData "uri"
				@setRoute (@getData("uri").replace /^\//, "")

		setRoute: (@route) ->
			if (@getData "modal")?
				@router.routeModalObject @route, this
			else
				@router.routeObject @route, this

		setActive: (@active) -> @delegate.setActive @active

		routeEvent: (matchedRoute, routeArgs) ->
			if @isMatch
				@isMatch = false

				if not @active then @activate.apply this, @matchArgs

				@lastMatchArgs = @matchArgs
				@matchArgs = null
			else
				if @active then @deactivate()

		routeMatchIfActive: ->
			@isMatch = @active
			@matchArgs = []

		routeMatch: (args...) ->
			@isMatch = true
			@matchArgs = args

		deactivate: ->
			@setActive false
			@trigger "deactivated", this
			@delegate.hide()

		activate: ->
			@setActive true
			@trigger "activated", this
			@delegate.show()

	exports.RecordView = class RecordView extends RouteableView
		constructor: ->
			super

			@fetchUrl = @getData "fetchUrl"

		modelFor: (@id) ->
			@model = new Backbone.Model id: @id
			@model.urlRoot = @fetchUrl

		activate: (id) ->
			@modelFor id

			@model.fetch()
				.done =>
					@render()
					RouteableView::activate.apply this, []
				.fail -> window.history.back()
				.progress (p...) -> console.log p

	exports.CollectionView = class CollectionView extends RouteableView
		shouldFetch: true

		events:
			"click [data-reload]": "reload"
			"click [data-sort]": "sort"

		constructor: ->
			super

			@itemTemplate = @getData "itemTemplate"
			@fetchUrl = @getData "fetchUrl"

			if (@getData "searchString")?
				@currentData = @getData "searchString"
				@currentData = @currentData.replace /\/$/, ""
			else
				@currentData = ""

			@shouldReload = false

		collectionFor: (@fetchData) ->
			@collection = new Backbone.Collection
			@collection.url = "#{@fetchUrl}/#{@fetchData}"

		template: -> @baseTemplate

		activate: (fetchData) ->
			fetchData = fetchData.replace /\/$/, ""

			if @currentData != fetchData or @shouldReload
				@collectionFor fetchData
				@currentData = fetchData
				@shouldReload = false
				@sync()

		reload: (ev) ->
			ev.preventDefault()
			@shouldReload = true
			@activate @currentData

		sort: (ev) ->
			ev.preventDefault()

			if not @collection?
				@shouldReload = true
				(@activate @currentData).then => @sort
					target: ev.target,
					preventDefault: ->
				return

			target = $ ev.target
			sortBy = target.data "sort"

			if sortBy[0] == "-"
				reverse = true
				sortBy = sortBy[1..]
				target.attr "data-sort", sortBy
			else
				reverse = false
				target.attr "data-sort", "-#{sortBy}"

			if sortBy[0] == "#"
				asDate = true
				sortBy = sortBy[1..]
			else
				asDate = false

			@collection.comparator = (m1, m2) ->
				v1 = m1.get "sort_#{sortBy}"
				v2 = m2.get "sort_#{sortBy}"
				
				if asDate
					v1 = new Date "#{v1}T12:00:00"
					v2 = new Date "#{v2}T12:00:00"

				# cmp = (v1 - v2) / Math.abs (v1 - v2)
				# -- would've been so nice if that worked on not-numbers...
				cmp = if v1 < v2 then -1 else if v1 > v2 then 1 else 0
				cmp = -1 * cmp if reverse
				cmp

			@collection.sort()

			@render()

		render: ->
			delete @subviews

			if @baseTemplate?
				(@delegate.update @template()).then =>
					@renderItems().then =>
						@subviews = @constructor.scanViews @router, @$el
			else
				@renderItems().then =>
					@subviews = @constructor.scanViews @router, @$el

		renderItems: ->
			target = @delegate.select "[data-container]"
			if target.length == 0 then target = @$el
			target.empty()
			
			if @collection.length > 0
				for i in [0..@collection.length - 1]
					model = @collection.at i
					view = new ItemView @router,
						template: @itemTemplate
						model: model

					view.render()

					target.append view.$el
				
				@delegate.update @$el.html()
			else
				(new $.Deferred).resolve()

		sync: ->
			@delegate.wait()
			@collection.fetch()
				.always => @delegate.stopWaiting()
				.done => @render()
				.fail -> window.history.back()
				.progress (p...) -> console.log p

	class ItemView extends View


	exports.RouterView = class RouterView extends View
		events:
			"click [data-router]": "route"

		constructor: ->
			super
			routers = @delegate.select "[data-router]"
			routers.on "click", @route.bind this


		route: (ev) ->
			ev.preventDefault()
			target = $ ev.target
			uri = target.data "routeUri"

			if not uri?
				uri = target.attr "href"

			@router.navigate uri, trigger: true

	exports.DynamicRouterView = class DynamicRouterView extends RouterView
		@dispatch: _.clone(Backbone.Events)

		constructor: ->
			super

			@group = @getData "group"
			@uriTemplate = @getData "uriTemplate"

			@listenTo @constructor.dispatch,
				"update:#{@group}", (data) => @update data

			@listenTo @constructor.dispatch,
				"updateUrl:#{@group}", (url) => @updateUrl url

		@updateAll: (group, data) ->
			DynamicRouterView.dispatch.trigger "update:#{group}", data

		@updateAllUrl: (group, url) ->
			DynamicRouterView.dispatch.trigger "updateUrl:#{group}", url

		update: (data) ->
			router = @delegate.select "[data-router]"
			newUri = swig.render @uriTemplate, locals: data
			newUri = newUri.replace /\/\//g, "/"
			router.data "routeUri", newUri
			if (router.attr "href")? then router.attr "href", newUri

		updateUrl: (url) ->
			router = @delegate.select "[data-router]"
			router.data "routeUri", url
			if (router.attr "href")? then router.attr "href", url



	exports.FormRouterView = class FormRouterView extends View
		@delegate: Delegates.FormDelegate

		updateAll: (data) ->
			tag = (@delegate.select "[data-update-group]").filter(":visible")

			if tag.length
				tag = tag.data "updateGroup"
				DynamicRouterView.updateAll tag, data

		updateAllUrl: (url) ->
			tagUrl = (@delegate.select "[data-update-group-url]")
				.filter(":visible")

			if tagUrl.length
				tagUrl = tagUrl.data "updateGroupUrl"
				DynamicRouterView.updateAllUrl tagUrl, url

		action: ->
			action = (@delegate.select "[data-action]").filter(":visible")

			if action.length then action.data "action" else @$el.attr "action"

		saveUrl: (url) ->
			saveUrlTo = (@delegate.select "[data-save-url-to]").filter(":visible")
			
			if saveUrlTo.length
				id = saveUrlTo.data "saveUrlTo"
				($ "##{id}").attr "href", url


		url: (data) -> swig.render @action(), locals: data

		events:
			"submit": "route"

		route: (ev) ->
			ev.preventDefault()
			data = @delegate.serialize()
			url = @url data
			@updateAll data
			@updateAllUrl url

			while url.match /\/\//
				url = url.replace /\/\//g, "/"

			# @saveUrl url
			@router.navigate url, trigger: true


	exports

