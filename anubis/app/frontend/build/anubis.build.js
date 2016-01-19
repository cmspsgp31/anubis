(
	{ baseUrl: "."
	, name: "anubis/main"
	, out: "anubis.js"
	, paths:
		{ "jquery": "../lib/jquery.min"
		, "ui": "../lib/jquery-ui.min"
		, "backbone": "../lib/backbone-min"
		, "swig": "../lib/swig.min"
		, "underscore": "../lib/underscore-min"
		, "requireLib": "../lib/require"
		}
	, map:
		{ "*": { "backbone": "anubis/csrf_backbone" }
		, "anubis/csrf_backbone": { "backbone": "backbone" }
		}
	, include: [ "requireLib", "anubis/token_view" ]
	}
)
