define [ "backbone"
	, "underscore"
	, "jquery"
	, "swig"
	, "anubis/delegates"
	, "anubis/models"],
(Backbone, _, $, swig, Delegates, Models) ->
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

				if @toTry.length == 0 then @promise.resolve()

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
			if @delegate? then delete @delegate
			@delegate = new (@delegateClass()) @$el, this

		template: ->
			swig.render (@constructor.templates.get @baseTemplate),
				locals: obj: @model.attributes

		render: ->
			if @baseTemplate?
				delete @subviews
				(@delegate.update @template()).then =>
					@subviews = @constructor.scanViews @router, @$el

		@scanViews: (router, parent, viewClasses) ->
			if not viewClasses? then viewClasses = {}
			_.extend viewClasses, exports

			views = []

			for el in $ "[data-view]", parent
				el = $ el
				viewName = el.data "view"
				options = el: el

				if el.data "delegate"
					options.delegateClass = Delegates[el.data "delegate"]

				views.push new viewClasses[viewName] router, options

			return views

		@error: (router, transport) ->
			errorEl = $ ".anubis-error"

			if transport.responseJSON
				($ "[data-error-name]", errorEl).html \
					transport.responseJSON.name
				($ "[data-error-description]", errorEl).html \
					transport.responseJSON.detail

			router.error = true

			window.history.back()

		@showError: -> ($ ".anubis-error").show()

		@hideError: -> ($ ".anubis-error").hide()


	exports.RouteableView = class RouteableView extends View
		isMatch: false
		active: false
		matchArgs: null
		lastMatchArgs: null

		constructor: (router, options) ->
			super

			if (@getData "active")? then @setActive true

			@autoRoute()

			@routing = null
			@router.on "route", (args...) => @routeEvent args

		newRouting: -> @routing = new $.Deferred

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

				if not @active then @activate.apply @, @matchArgs
				else @resolveRouting()

				@lastMatchArgs = @matchArgs
				@matchArgs = null
			else
				if @active then @deactivate()

		routeMatchIfActive: ->
			@isMatch = @active
			@matchArgs = []
			@newRouting()
			if not @active then @routing.resolve()
			@routing

		routeMatch: (args...) ->
			@isMatch = true
			@matchArgs = args
			@newRouting()

		resolveRouting: ->
			if @routing?
				@routing.resolve @route
				@routing = null

		deactivate: ->
			@setActive false
			@trigger "deactivated", this
			@delegate.hide()

		activate: ->
			@setActive true
			@trigger "activated", this
			@delegate.show()
			@resolveRouting()

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
				.always => @resolveRouting()
				.fail (t) => @constructor.error @router, t
				.progress (p...) -> console.log p

	exports.CollectionView = class CollectionView extends RouteableView
		@delegate = Delegates.CollectionDelegate
		shouldFetch: true

		events:
			"click [data-reload]": "reload"
			"click [data-action]": "actionWithResults"
			"click [data-sort]": "naiveSort"

		constructor: ->
			super

			@cache = if (@getData "cache")? then {} else null

			@retrieveTemplate = @getData "retrieveTemplate"
			
			if (@getData "currentData")?
				@currentData = @getData "currentData"
			else
				@currentData = ""?

			if (@getData "modelsAt")?
				@modelsAt = @getData "modelsAt"

			@usesPagination = (@getData "paginate")?

			if @usesPagination then @preparePagination()

			@usesDynamicTemplates = (@getData "itemTemplateIndex")?

			if @usesDynamicTemplates
				@_itemTemplate = parseInt (@getData "itemTemplateIndex")
			else
				@_itemTemplate = @getData "itemTemplate"

			@usesCustomActions = \
				(@delegate.select "[data-actions-list]").length > 0

			@shouldReload = false

			@loading = null

		preparePagination: ->
			@delegate.preparePagination()
			@activateTemplate = @getData "activateTemplate"

			if (@getData "currentPage")?
				@currentPage = parseInt (@getData "currentPage")
			else
				@currentPage = 1

			@nextPage = @currentPage + 1
			@totalPages = parseInt (@getData "totalPages")
			@totalObjects = parseInt (@getData "totalObjects")
			@hasNextPage = not ((@getData "lastPage")?)
			@objectsPerPage = parseInt (@getData "objectsPerPage")

			@_pageTemplate = parseInt (@getData "pageTemplateIndex")

			pageListParent = (@delegate.select "[data-page-list]").parent()
			pageListParent.on "show.bs.dropdown", => @delegate.createPageLinks()

			@showOrHideNext()

			if @currentPage != 1 then @delegate.moveToPage @currentPage

			@delegate.updateTotalObjects @totalObjects

		retrieveUrl: ->
			swig.render @retrieveTemplate, locals: args: @retrieveData

		itemTemplate: ->
			if @usesDynamicTemplates
				@retrieveData[@_itemTemplate]
			else
				@_itemTemplate

		collectionFor: (retrieveUrl) ->
			@collection = new Models.ExtendedCollection
			if @modelsAt? then @collection.modelListProperty = @modelsAt
			@collection.url = retrieveUrl

		template: -> @baseTemplate

		activate: (@retrieveData...) ->
			retrieveUrl = @retrieveUrl()

			differentData = @currentData != retrieveUrl
			haveCache = @cache?
			inCache = if haveCache then (retrieveUrl in _.keys @cache) else false
			shouldReload = @shouldReload

			@currentData = retrieveUrl
			@shouldReload = false

			if not differentData and not shouldReload
				@resolveRouting()
			else if differentData and not shouldReload and haveCache and
					inCache
				@collection = @cache[retrieveUrl]
				@render()
			else if shouldReload and haveCache and inCache
				if differentData then @collection = @cache[retrieveUrl]
				@sync()
			else
				@collectionFor retrieveUrl

				if haveCache then @cache[retrieveUrl] = @collection

				@sync()

		gotoNextPage: ->
			if @hasNextPage
				@gotoPage @nextPage
			else
				resolved = new $.Deferred
				resolved.resolve()
				resolved

		gotoLastPage: ->
			if @hasNextPage
				@gotoPage @totalPages
			else
				resolved = new $.Deferred
				resolved.resolve()
				resolved


		gotoPage: (page) ->
			newData = @retrieveData[0..]
			newData[@_pageTemplate] = page
			url = swig.render @activateTemplate, locals: args: newData

			routePromise = @router.navigate url,
				trigger: true
				replace: true

			pagePromise = new $.Deferred

			routePromise.then =>
				(@delegate.moveToPage @currentPage).then ->
					pagePromise.resolve()

			pagePromise


		sync: ->
			@delegate.wait()
			@collection.fetch()
				.always => @delegate.stopWaiting()
				.done => @render()
				.fail (t) => @constructor.error @router, t
				.progress (p...) -> console.log p

		updatePaginationInfo: ->
			@currentPage = @collection.properties.current_page
			@hasNextPage = not @collection.properties.last_page
			@totalPages = @collection.properties.total_pages
			@totalObjects = @collection.properties.total_objects
			@nextPage = @currentPage + 1
			@showingRecords = @collection.size()

			@delegate.updateTotalObjects @totalObjects
			@delegate.updateShowing @showingRecords
			@delegate.updateCurrentPage @currentPage
			@delegate.updateTotalPages @totalPages

			@showOrHideNext()

		showOrHideNext: ->
			if @hasNextPage
				@delegate.paginationTrigger.show()
			else
				@delegate.paginationTrigger.hide()

		render: ->
			if @collection.properties?
				if @usesPagination then @updatePaginationInfo()
				if @usesCustomActions
					if "actions" in _.keys @collection.properties
						@delegate.setActions @collection.properties.actions
					else
						@delegate.setActions []

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
				end_range = @collection.length - 1
				contents = (@renderSingleItem @itemTemplate(), i, end_range \
					for i in [0..end_range])

				target.html contents.join ""
				@delegate.found()
			else
				@delegate.notFound()

			promise = @resolveRouting()

			if not promise?
				promise = new $.Deferred
				promise.resolve()

			promise

		renderSingleItem: (templateName, index, end_range) ->
			model = @collection.at index
			template = @constructor.templates.get templateName
			item = ""

			if @usesPagination
				page = index / @objectsPerPage + 1

				if index % @objectsPerPage == 0
					item = @delegate.anchorForPage page

			item += swig.render template, locals:
				obj: model.attributes
				loop:
					first: index == 0
					last: index == end_range
					index: index + 1
					index0: index
					key: index

		reload: (ev) ->
			ev.preventDefault()
			@shouldReload = true
			@activate @retrieveData...

		naiveSort: (ev) ->
			target = $ ev.target
			@collection.comparator = target.data "sort"
			@collection.sort()
			@render()

		actionWithResults: (ev) ->
			ev.preventDefault()

			if not @collection?
				(@reload ev).then => @actionWithResults ev
			else
				actionTag = $ ev.target
				actionUrl = actionTag.data "action"
				actionTemplate = actionTag.data "response"

				view = new ActionView @router,
					actionUrl: actionUrl
					template: actionTemplate
					collection: @collection

	exports.ActionView = class ActionView extends View
		@delegate = Delegates.UnroutedModalDelegate

		events:
			"click button[data-submit]": "sendForm"

		constructor: ->
			super

			@actionUrl = @getData "actionUrl"
			@collection = @getData "collection"
			@_idList = @getData "idList"
			@model = {}

			@performAction()

		idList: -> (m.id for m in @collection.models).join ','

		performAction: (data) ->
			if not data?
				data = collection: "[#{@idList()}]"

			$.ajax @actionUrl,
				data: data
				type: "POST"
				beforeSend: (xhr) ->
					token = $('meta[name="csrf-token"]').attr "content"
					xhr.setRequestHeader "X-CSRFToken", token
				success: (data) => @dispatch data
				error: (jqxhr, _, error) =>
					data = jqxhr.responseJSON

					if not data?
						@actionResponse \
							"Erro HTTP #{jqxhr.status}: #{error}"
					else
						@actionResponse \
							"#{data["name"]}: #{data["detail"]}", false

		dispatch: (data) ->
			switch data["result"]
				when "action"
					@actionResponse data["reason"], data["success"]
				when "invalid_form", "requires_data"
					@showForm data, data["result"] == "requires_data"
				else
					console.log data

		actionResponse: (reason, success) ->
			_.extend @model,
				form: null
				reason: reason
				success: success
				processing: false

			@show()

		showForm: (data, failure) ->
			_.extend @model,
				title: data["title"]
				description: data["description"]
				form: "<form data-action-form>#{data["form"]}</form>"
				reason: null
				processing: false

			for cssUrl in data["css"]
				if ($ "link[href='#{cssUrl}']").length == 0
					css = $ "<link/>",
						rel: "stylesheet"
						type: "text/css"
						href: cssUrl

					css.appendTo "head"

			for jsUrl in data["js"]
				if ($ "script[src='#{jsUrl}']").length == 0
					js = $ "<script></script>",
						type: "text/javascript"
						src: jsUrl

					js.appendTo "head"

			@show()

		setupForm: (form) ->
			form.attr "action", @actionUrl
			form.attr "method", "POST"
			form.on "submit", (ev) =>
				ev.preventDefault()
				@sendForm ev

		sendForm: (ev) ->
			_.extend @model, processing: true

			form = @delegate.select "form[data-action-form]"
			@performAction form.serialize()

			@render()

		destroy: -> if not @model.processing then @delegate.remove()

		template: ->
			swig.render (@constructor.templates.get @baseTemplate),
				locals: @model

		show: ->
			@delegate.insert()

			doShow = =>
				@render()
				@delegate.show().then =>
					form = @delegate.select "form[data-action-form]"
					@setupForm form

			if @delegate.visible then @delegate.hide().then doShow
			else doShow()



	exports.RouterView = class RouterView extends View
		events:
			"click [data-router]": "route"
			"click [data-should-mark-as-visited]": "markAsVisited"

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

			@markAsVisited()

			@router.navigate uri, trigger: true

		markAsVisited: ->
			(@delegate.select "a[data-mark-as-visited]").addClass "visited"

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

	exports.RouteableFieldView = class RouteableFieldView extends RouteableView
		constructor: ->
			super

			if (@getData "fieldIndex")?
				@fieldIndex = @getData "fieldIndex"
			else
				@fieldIndex = 0

			@addSlash = (@getData "addSlash")?

		activate: (args...) ->
			name = @$el.attr "name"
			value = args[@fieldIndex]

			if @addSlash then value = "/" + value

			for form in $ "form"
				if $.contains form, @el
					($ "[name=#{name}]", ($ form)).val [value]

			@resolveRouting()

		deactivate: ->

	exports.FormRouterView = class FormRouterView extends View
		@delegate: Delegates.FormDelegate


		constructor: ->
			super

			@router.on "route", (args...) =>
				@delegate.disable()
				@router.routing.then => @delegate.enable()

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

			@router.navigate url, trigger: true


	exports

