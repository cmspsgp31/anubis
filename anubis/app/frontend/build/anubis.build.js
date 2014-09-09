(
	{ baseUrl: "."
	, name: "anubis/main"
	, out: "../../static/anubis/anubis.js"
	, paths:
		{ "jquery": "empty:"
		, "backbone": "lib/backbone"
		, "swig": "lib/swig"
		, "underscore": "lib/underscore"
		, "requireLib": "lib/require"
		}
	, map:
		{ "*": { "backbone": "anubis/csrf_backbone" }
		, "anubis/csrf_backbone": { "backbone": "backbone" }
		}
	, include: [ "requireLib" ]
	}
)
