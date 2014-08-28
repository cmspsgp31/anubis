# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# filter_view.py - Django View que suporta filtros arbitrários.

# Este arquivo é parte do software django_procedures.

# django_procedures é um software livre: você pode redistribuí-lo e/ou
# modificá-lo sob os termos da Licença Pública Geral GNU (GNU General Public
# 		License), tal como é publicada pela Free Software Foundation, na
# versão 3 da licença, ou (sua decisão) qualquer versão posterior.

# django_procedures é distribuído na esperança de que seja útil, mas SEM NENHUMA
# GARANTIA; nem mesmo a garantia implícita de VALOR COMERCIAL ou ADEQUAÇÃO PARA
# UM PROPÓSITO EM PARTICULAR. Veja a Licença Pública Geral GNU para mais
# detalhes.

# Você deve ter recebido uma cópia da Licença Pública Geral GNU junto com este
# programa. Se não, consulte <http://www.gnu.org/licenses/>.

from django_procedures.query import ProcedureQuerySet
from django.db.models.query import Q
from functools import reduce

import operator

class Filter:
	def filter_queryset(self, queryset, args):
		raise NotImplementedError()

class ProcedureFilter(Filter):
	def __init__(self, procedure_name):
		super().__init__()
		self.procedure_name = procedure_name

	def filter_queryset(self, queryset, args):
		assert isinstance(queryset, ProcedureQuerySet)

		return queryset.procedure(self.procedure_name, *args)

class QuerySetFilter(Filter):
	def __init__(self, field_name, suffix="", connector=operator.or_):
		super().__init__()
		self.field_name = field_name
		self.connector = connector
		self.suffix = suffix

	def filter_queryset(self, queryset, args):
		query_field = "{}__{}".format(self.field_name, self.suffix)
		complex_filter = [Q(**{query_field: arg}) for arg in args]

		return queryset.filter(reduce(self.connector, complex_filter))

class query_string_parser:
	quote_char = "\""
	sep_char = ","
	escape_char = "$"

	def __init__(self, filter_mark):
		self.filters = []
		self.filter_args = None
		self.current_arg = None
		self.filter_mark = filter_mark
		self.context = None

		self.context_map = \
			{ "no_filter" : \
				[ self._context_no_filter_filter_mark
				, self._context_no_filter_any
				]
			, "filter_no_arg": [ self._context_filter_no_arg_any ]
			, "filter_arg_no_quote" : \
				[ self._context_filter_arg_no_quote_filter_mark
				, self._context_filter_arg_no_quote_separator
				, self._context_filter_arg_no_quote_any
				]
			, "filter_arg_quote" : \
				[ self._context_filter_arg_quote_escape
				, self._context_filter_arg_quote_quote
				, self._context_filter_arg_quote_any
				]
			, "filter_no_arg_next_arg" : \
				[ self._context_filter_no_arg_next_arg_filter_mark
				, self._context_filter_no_arg_next_arg_separator
				, self._context_filter_no_arg_next_arg_any
				]
			}

	def _context_no_filter_filter_mark(self, char, query_string):
		query_string = query_string.lstrip(self.filter_mark)
		self.filter_args = []
		self.context = "filter_no_arg"

		return query_string

	_context_no_filter_filter_mark.match = \
		lambda s, _, q: q.startswith(s.filter_mark)

	def _context_no_filter_any(self, char, query_string):
		return query_string[1:]

	_context_no_filter_any.match = lambda _, __, ___: True

	def _context_filter_no_arg_any(self, char, query_string):
		inside_quote = char == self.quote_char
		self.current_arg = "" if inside_quote else char
		self.context = "filter_arg"
		self.context += "_quote" if inside_quote else "_no_quote"

		return query_string[1:]

	_context_filter_no_arg_any.match = lambda _, __, ___: True

	def _context_filter_arg_no_quote_filter_mark(self, char, query_string):
		self._close_filter()

		return query_string[1:]

	_context_filter_arg_no_quote_filter_mark.match = \
		lambda s, _, q: q.startswith(s.filter_mark)

	def _context_filter_arg_no_quote_separator(self, char, query_string):
		self._close_arg()

		return query_string[1:]

	_context_filter_arg_no_quote_separator.match = \
		lambda s, c, _: c == s.sep_char

	def _context_filter_arg_no_quote_any(self, char, query_string):
		self.current_arg += char

		return query_string[1:]

	_context_filter_arg_no_quote_any.match = lambda _, __, ___: True

	def _context_filter_arg_quote_escape(self, char, query_string):
		if len(query_string) > 1:
			query_string = query_string[1:]
			char = query_string[0]

		self.current_arg += char

		return query_string[1:]

	_context_filter_arg_quote_escape.match = \
		lambda s, c, _: c == s.escape_char

	def _context_filter_arg_quote_quote(self, char, query_string):
		self._close_arg()
		self.context = "filter_no_arg_next_arg"

		return query_string[1:]

	_context_filter_arg_quote_quote.match = \
		lambda s, c, _: c == s.quote_char

	def _context_filter_arg_quote_any(self, char, query_string):
		self.current_arg += char

		return query_string[1:]

	_context_filter_arg_quote_any.match = lambda _, __, ___: True

	def _context_filter_no_arg_next_arg_filter_mark(self, char, query_string):
		self._close_filter()
		return self._context_no_filter_filter_mark(char, query_string)

	_context_filter_no_arg_next_arg_filter_mark.match = \
		lambda s, _, q: q.startswith(s.filter_mark)


	def _context_filter_no_arg_next_arg_separator(self, char, query_string):
		if len(query_string) > 1:
			query_string = query_string[1:]
			return self._context_filter_no_arg_any(query_string[0],
				query_string)
		else:
			return query_string[1:]

	_context_filter_no_arg_next_arg_separator.match = \
		lambda s, c, _: c == s.sep_char

	def _context_filter_no_arg_next_arg_any(self, char, query_string):
		return query_string[1:]

	_context_filter_no_arg_next_arg_any.match = lambda _, __, ___: True

	def _close_arg(self):
		if self.current_arg is not None:
			self.filter_args.append(self.current_arg)

		self.current_arg = None
		self.context = "filter_no_arg"

	def _close_filter(self):
		self._close_arg()

		if self.filter_args is not None and len(self.filter_args) > 0:
			self.filters.append(self.filter_args)

		self.filter_args = None
		self.context = "no_filter"

	def parse(self, query_string):
		self.filters = []
		self.filter_args = None
		self.current_arg = None
		self.context = "no_filter"

		while len(query_string) > 0:
			char = query_string[0]

			for proc in self.context_map[self.context]:
				if proc.match(self, char, query_string):
					print(proc.__name__)
					query_string = proc(char, query_string)
					break

		self._close_filter()

		return self.filters

def _parse_filter(filter_):
	args = []
	elem = None
	quote = False

	i = 0

	def advance(i, string):
		return (i+1, string[i+1])

	while i < len(filter_):
		char = filter_[i]

		if elem is None:
			quote = char == "\""
			elem = "" if quote else char
		else:
			if not quote:
				if char == ",":
					args.append(elem)
					elem = None
				else:
					elem += char
			else:
				if char == "$":
					if i < len(filter_) - 1:
						i, char = advance(i, filter_)

					elem += char
				elif char == "\"":
					while not char == "," and i < len(filter_) - 1:
						i, char = advance(i, filter_)

					args.append(elem)
					elem = None
					quote = False
				else:
					elem += char

		i += 1

	if elem is not None:
		args.append(elem)

	return args

class FilterViewMixin:
	prefix = "filter"
	kwarg_key = "search"
	allowed_filters = {}

	def _get_queryset_filter(self, queryset, url):
		url = url.strip()
		url = url.rstrip("/")
		parser = query_string_parser("/{}/".format(self.prefix))

		print(url)
		for args in parser.parse(url):
			print(args)
			# args = _parse_filter(filter_)

			if len(args):
				queryset = self._apply_filter(queryset, args)

		return queryset

	def get_queryset(self):
		# MRO do Python garante que haverá um get_queryset definido aqui se
		# FilterViewMixin for declarado como class pai antes da classe de View.
		original = super().get_queryset()

		if self.kwarg_key in self.kwargs.keys() and self.kwargs[self.kwarg_key]:
			return self._get_queryset_filter(original,
				self.kwargs[self.kwarg_key])
		else:
			return original.none()

	def _apply_filter(self, queryset, args):
		filter_name = args.pop(0)

		if not filter_name in self.allowed_filters.keys():
			raise ValueError("{} is not an allowed filter." \
				.format(filter_name))

		return self.allowed_filters[filter_name].filter_queryset(queryset, args)

