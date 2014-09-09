define ["backbone", "underscore", "anubis/views"], (Backbone, _, Views) ->
	class ObjectRouter extends Backbone.Router
		@lastNonModalMatch = null

		constructor: ->
			super
			@route /^(.*)$/, "", @routeEvent

		_objRoutes:
			"":
				route: ""
				objects: []

		_modalRoutes: {}

		routeEvent: (route, args...) ->
			modalMatch = false
			
			for routeName, routeInfo of @_modalRoutes
				matches = route.match routeInfo.route
				if matches? and matches.length > 0
					obj = routeInfo.object
					obj.routeMatch.apply obj, matches[1..]
					modalMatch = true
					break

			for routeName, routeInfo of @_objRoutes
				if modalMatch
					for obj in routeInfo.objects
						obj.routeMatchIfActive()
				else
					matches = route.match routeInfo.route
					if matches? and matches.length > 0
						@lastNonModalMatch = route
						for obj in routeInfo.objects
							obj.routeMatch.apply obj, matches[1..]


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
