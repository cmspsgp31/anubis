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

from django.db.models.expressions import RawSQL


class ProcedureOrderingAnnotation(RawSQL):
    template = (
        "(select {function}_res.rank "
        "from {function}({args}) as {function}_res "
        "where {field} = {function}_res.id)"
    )

    def __init__(self, function, *args, lookup="id", **kwargs):
        self.name = function
        self.col_name = lookup
        self.col = self._parse_expressions(lookup)[0]

        super().__init__("", args)

    def resolve_expression(self, query=None, allow_joins=True, reuse=None,
                           summarize=False, for_save=False):
        clone = self.copy()
        clone.is_summary = summarize
        clone.col = clone.col.resolve_expression(query, allow_joins, reuse,
                                                 summarize, for_save)

        return clone

    @property
    def default_alias(self):
        return "{}_{}".format(self.col_name, self.name.lower())

    def as_sql(self, compiler, connection):
        field_name, _ = compiler.compile(self.col)

        args = list(self.params)

        arg_marks = ", ".join(["%s"] * len(args))

        self.sql = self.template.format(function=self.name, args=arg_marks,
                                        field=field_name)

        return super().as_sql(compiler, connection)

ProcedureAggregate = ProcedureOrderingAnnotation
# backwards compatibility

def test():
    from bases_cmsp.eventos.models import Evento

    print(str(Evento.objects.order_by_procedure("agg_test", "id", "dia").distinct().query))
