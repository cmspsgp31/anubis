define ["backbone"
	, "underscore"
	, "anubis/views"
	, "anubis/router"
	, "anubis/delegates"
	, "anubis/token_view"
	, "swig"],
(Backbone, _, Views, Router, Delegates, TokenView, swig) ->
	_.templateSettings =
		interpolate: /\[\[(.+?)\]\]/g
		escape: /\[\-(.+?)\]\]/g
		evaluate: /\[\=(.+?)\]\]/g

	swig.setFilter "getitem", (input, key) -> input[key]
	swig.setFilter "length", (input) -> input.length
	swig.setFilter "divisibleby", (input, num) -> ((input % num) == 0)

	start = (historyArgs) ->
		for t in $("link[data-template]")
			t = $ t
			Views.View.templates.request (t.attr "href")

		Views.View.templates.pull().done ->
			router = new Router.ObjectRouter
		
			views = Views.View.scanViews router, ($ "body"), TokenView

			Backbone.history.start historyArgs
	start: start




