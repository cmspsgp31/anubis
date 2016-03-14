(
	{ baseUrl: "."
	, name: "anubis/main"
	, out: "anubis.js"
	, paths:
		{ "jquery": "../lib/jquery"
		, "ui": "../lib/jquery-ui"
		, "backbone": "../lib/backbone"
		, "swig": "../lib/swig"
		, "underscore": "../lib/underscore"
		, "requireLib": "../lib/require"
		}
	, map:
		{ "*": { "backbone": "anubis/csrf_backbone" }
		, "anubis/csrf_backbone": { "backbone": "backbone" }
		}
	, include: [ "requireLib", "anubis/token_view" ]
	}
)
