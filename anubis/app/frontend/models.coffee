define ["backbone", "underscore"], (Backbone, _) -> exports =
	ExtendedCollection: class ExtendedCollection extends Backbone.Collection
		constructor: ->
			super
			@modelListProperty = "data"

		set: (models, options) ->
			if not (_.isArray models)
				@properties = models
				models = models[@modelListProperty]

			super models, options


