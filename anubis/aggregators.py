# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# aggregators.py - Agregadores de expressões booleanas.

# Este arquivo é parte do software Anubis.

# Anubis é um software livre: você pode redistribuí-lo e/ou modificá-lo
# sob os termos da Licença Pública Geral GNU (GNU General Public License),
# tal como é publicada pela Free Software Foundation, na versão 3 da
# licença, ou (sua decisão) qualquer versão posterior.

# Anubis é distribuído na esperança de que seja útil, mas SEM NENHUMA
# GARANTIA; nem mesmo a garantia implícita de VALOR COMERCIAL ou ADEQUAÇÃO
# PARA UM PROPÓSITO EM PARTICULAR. Veja a Licença Pública Geral GNU para
# mais detalhes.

# Você deve ter recebido uma cópia da Licença Pública Geral GNU junto com
# este programa. Se não, consulte <http://www.gnu.org/licenses/>.

from anubis.url import Boolean

class Aggregator:
	def __init__(self):
		pass

	@staticmethod
	def need_parenthesis(outside, inside):
		outside_precedence = Boolean.precedence.index(outside)
		inside_precedence = Boolean.precedence.index(inside)

		return outside_precedence < inside_precedence

	def __call__(self, base_expression=None, not_expression=None,
			and_expression=None, or_expression=None, inside_type=None,
			left_type=None, right_type=None):

		if base_expression is not None:
			return self.handle_base_expression(base_expression)
		elif not_expression is not None:
			need_parens = self.need_parenthesis(Boolean.Not, inside_type)
			return self.handle_not_expression(not_expression, need_parens)
		elif and_expression is not None:
			left_expr, right_expr = and_expression
			left_parens = self.need_parenthesis(Boolean.And, left_type)
			right_parens = self.need_parenthesis(Boolean.And, right_type)
			return self.handle_and_expression(left_expr, right_expr,
				left_parens, right_parens)
		elif or_expression is not None:
			left_expr, right_expr = or_expression
			left_parens = self.need_parenthesis(Boolean.Or, left_type)
			right_parens = self.need_parenthesis(Boolean.Or, right_type)
			return self.handle_or_expression(left_expr, right_expr,
				left_parens, right_parens)
		else:
			return self.handle_impossible_case()

	def handle_base_expression(self, base_expression):
		raise NotImplementedError()

	def handle_not_expression(self, not_expression, need_parens):
		raise NotImplementedError()

	def handle_and_expression(self, left_expression, right_expression,
			left_parens, right_parens):
		raise NotImplementedError()

	def handle_or_expression(self, left_expression, right_expression,
			left_parens, right_parens):
		raise NotImplementedError()

	def handle_impossible_case(self):
		raise RuntimeError()

class QuerySetAggregator(Aggregator):
	def __init__(self, base_queryset, allowed_filters):
		super().__init__()
		self.base_queryset = base_queryset
		self.allowed_filters = allowed_filters

	def handle_base_expression(self, base_expression):
		filter_ = self.allowed_filters[base_expression["field"]]
		args = base_expression["args"]
		return filter_.filter_queryset(self.base_queryset, args)

	def handle_not_expression(self, not_expression, _):
		return self.base_queryset.exclude(id__in=not_expression.values("id"))

	def handle_and_expression(self, left_expression, right_expression, _, __):
		return left_expression & right_expression

	def handle_or_expression(self, left_expression, right_expression, _, __):
		return left_expression | right_expression

	def handle_impossible_case(self):
		return self.base_queryset

class TokenAggregator(Aggregator):
	def __init__(self, allowed_filters):
		super().__init__()
		self.allowed_filters = allowed_filters

	@classmethod
	def open_close_parens(cls, needed):
		parens_open = ""
		parens_close = ""

		if needed:
			parens_open = cls.make_token("open")
			parens_close = cls.make_token("close")

		return (parens_open, parens_close)

	@staticmethod
	def make_token(name, contents="", attributes={}):
		attrs = ""

		if len(attributes) > 0:
			attrs = " ".join(["{}=\"{}\"".format(k, v) \
					for k, v in attributes.items()])
			attrs = " {}".format(attrs)

		return """<li data-token="{name}"{attrs}>
			<p>{contents}</p>
			<button type="button" class="close" tabindex="-1" data-remove>&times;</button>
			</li>""" \
			.format(name=name, contents=contents, attrs=attrs)

	def handle_base_expression(self, base_expression):
		filter_ = self.allowed_filters[base_expression["field"]]
		args = base_expression["args"]
		form = filter_.bound_form(args)

		if len(args) == 1:
			hide_legend = " style=\"display: none;\""
		else:
			hide_legend = ""
		
		contents = """
			<fieldset>
			<div class="legend"{hide_legend}>{full_name}</div>
			{rendered_form}
			</fieldset>
		""".format(hide_legend=hide_legend, rendered_form=form.as_p(),
				full_name=filter_.description)

		return self.make_token("expression", contents,
			{"data-name": filter_.identifier})

	def handle_not_expression(self, not_expression, need_parens):
		parens_open, parens_close = self.open_close_parens(need_parens)

		return """
		{negate_token}
		{parens_open}
		{expression}
		{parens_close}
		""".format(expression=not_expression, parens_open=parens_open,
			parens_close=parens_close, negate_token=self.make_token("negate"))

	def handle_and_expression(self, left_expression, right_expression,
			left_parens, right_parens):
		left_open, left_close = self.open_close_parens(left_parens)
		right_open, right_close = self.open_close_parens(right_parens)

		return """
		{left_open}
		{left}
		{left_close}
		{and_token}
		{right_open}
		{right}
		{right_close}
		""".format(left=left_expression, right=right_expression,
			left_open=left_open, left_close=left_close, right_open=right_open,
			right_close=right_close, and_token=self.make_token("and"))

	def handle_or_expression(self, left_expression, right_expression,
			left_parens, right_parens):
		left_open, left_close = self.open_close_parens(left_parens)
		right_open, right_close = self.open_close_parens(right_parens)

		return """
		{left_open}
		{left}
		{left_close}
		{or_token}
		{right_open}
		{right}
		{right_close}
		""".format(left=left_expression, right=right_expression,
			left_open=left_open, left_close=left_close, right_open=right_open,
			right_close=right_close, or_token=self.make_token("or"))

