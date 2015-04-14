define ["backbone", "underscore", "anubis/views"], (Backbone, _, Views) ->
	class ObjectRouter extends Backbone.Router
		@lastNonModalMatch = null

		constructor: ->
			super
			@error = false
			@route /^(.*)$/, "", @routeEvent
			@routing = new $.Deferred
			@routing.resolve()

		_objRoutes:
			"":
				route: ""
				objects: []

		_modalRoutes: {}

		navigate: (url, options={}) ->
			options =
				trigger: options.trigger ? false
				replace: options.replace ? false

			if @routing.state() != "pending"
				{trigger, replace} = options
				@routing = new $.Deferred

				super "/",
					trigger: false
					replace: replace

				super url,
					trigger: trigger
					replace: true

				@routing
			else
				routeAgain = new $.Deferred
				routeAgain.reject()

				routeAgain


		routeEvent: (route, args...) ->
			if @error
				Views.View.showError()
				@error = false
			else
				Views.View.hideError()

			modalMatch = false
			promises = []

			for routeName, routeInfo of @_modalRoutes
				matches = route.match routeInfo.route
				if matches? and matches.length > 0
					obj = routeInfo.object
					promises.push obj.routeMatch.apply obj, matches[1..]
					modalMatch = true
					break

			for routeName, routeInfo of @_objRoutes
				if modalMatch
					for obj in routeInfo.objects
						promises.push obj.routeMatchIfActive()
				else
					matches = route.match routeInfo.route
					if matches? and matches.length > 0
						@lastNonModalMatch = route
						for obj in routeInfo.objects
							promises.push obj.routeMatch.apply obj, matches[1..]

			if @routing?
				promises = $.when promises...
				promises.then => @routing.resolve()


		routeFor: (objs) ->
			(args...) -> (obj.routeMatch.apply obj, args for obj in objs)

		routeModalObject: (route, object) ->
			routeName = @routeName route

			if routeName in _.keys(@_objRoutes) then return
			
			if not (routeName in _.keys(@_modalRoutes))
				@_modalRoutes[routeName] =
					route: route
					object: object
			

		routeObject: (route, object) ->
			routeName = @routeName route

			if not @_objRoutes[routeName]?
				@_objRoutes[routeName] =
					route: route
					objects: []

			if not _.has @_objRoutes[routeName].objects, object
				@_objRoutes[routeName].objects.push object

		routeName: (r) -> if r instanceof RegExp then r.toString() else r

		unrouteObject: (route, object) ->
			routeName = @routeName route

			if @_objRoutes[routeName]?
				@_objRoutes[routeName].objects = _.reject(
					@_objRoutes[routeName].objects, (v) -> v == object)

		unroute: (route) ->
			routeName = @routeName route

			if @_objRoutes[routeName]?
				@_objRoutes[routeName].objects = []

	ObjectRouter: ObjectRouter
