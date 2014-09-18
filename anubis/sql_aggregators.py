# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# sql_aggregators.py - Agregadores de SQL para Django

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

from django.db.models.sql.aggregates import Aggregate as SqlAggregate
from django.db.models.aggregates import Aggregate

class ProcedureSqlAggregate(SqlAggregate):
	sql_template = """
		(select {function}_res.rank
		from {function}({args}) as {function}_res
		where {field} = {function}_res.id)
	""".strip()

	def __init__(self, col, source=None, is_summary=False, **extra):
		self.sql_function = extra.pop("function")
		self.args = extra.pop("args")

		super().__init__(col, source, is_summary, **extra)

	def as_sql(self, qn, connection):
		if isinstance(self.col, (list, tuple)):
			field_name = '.'.join(qn(c) for c in self.col)
		else:
			field_name = qn(self.col)

		args = list(self.args)

		arg_marks = ", ".join(["%s"] * len(args))

		params = args

		return self.sql_template.format(function=self.sql_function,
			args=arg_marks, field=field_name), params

class ProcedureAggregate(Aggregate):
	def __init__(self, function, *args, lookup="id", **kwargs):
		kwargs.update({ 'function': function, 'args': args })
		super().__init__(lookup, **kwargs)
		self.name = function

	@property
	def default_alias(self):
		return "{}_{}".format(self.lookup, self.name.lower())

	def add_to_query(self, query, alias, col, source, is_summary):
		aggregate = ProcedureSqlAggregate(col, source=source,
			is_summary=is_summary, **self.extra)

		query.aggregates[alias] = aggregate


def test():
	from bases_cmsp.eventos.models import Evento

	print(str(Evento.objects.order_by_procedure("agg_test", "id", "dia").distinct().query))
