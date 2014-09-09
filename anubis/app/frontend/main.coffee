define ["backbone", "underscore", "anubis/views", "anubis/router", "anubis/delegates", "swig"], (Backbone, _, Views, Router, Delegates, swig) ->
	_.templateSettings =
		interpolate: /\[\[(.+?)\]\]/g
		escape: /\[\-(.+?)\]\]/g
		evaluate: /\[\=(.+?)\]\]/g

	start = (historyArgs) ->
		for t in $("link[data-template]")
			t = $ t
			Views.View.templates.request (t.attr "href")

		Views.View.templates.pull().done ->
			router = new Router.ObjectRouter
		
			views = Views.View.scanViews router, $ "body"

			Backbone.history.start historyArgs
	
	start: start




