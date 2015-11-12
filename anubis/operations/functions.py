# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# functions.py - operações de migração de funções de PostgreSQL.

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

"""
    Operações de migração de funções de PostgreSQL.
"""

from django.db.migrations.operations.base import Operation

class AddFunction(Operation):
    reduces_to_sql = True
    reversible = True

    def __init__(self, model, function_name, arguments,
                 return_value, function_body):
        self.model = model
        self.table_name = self.model._meta.db_table
        self.arguments = ", ".join(arguments)
        self.function_name = "{}_{}".format(self.table_name, function_name)
        self.return_value = return_value
        self.function_body = function_body

    def get_full_name(self):
        return "{}({})".format(self.function_name, self.arguments)

    def get_full_body(self):
        sql = """
            create or replace function {full_name}
            returns {return_value} as $$
            begin
                {function_body}
            end;
            $$ language plpgsql;
        """

        return sql.format(full_name=self.get_full_name(),
                          return_value=self.return_value,
                          function_body=self.function_body)

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, from_state,
                          to_state):
        body = self.get_full_body()
        schema_editor.execute(body)

    def database_backwards(self, app_label, schema_editor, from_state,
                           to_state):

        schema_editor.execute("drop function {};".format(self.get_full_name()))

    def describe(self):
        return "Creates function {}.".format(self.get_full_name())


class AddSearchFunction(AddFunction):
    reduces_to_sql = True
    reversible = True

    def __init__(self, model, function_name, arguments, query):
        return_value = "table(id int)"
        function_body = "return query {}".format(query)

        super().__init__(model, function_name, arguments, return_value,
                         function_body)


class AddSortFunction(AddFunction):
    reduces_to_sql = True
    reversible = True

    def __init__(self, model, function_name, arguments, query):
        return_value = "table(id int, rank numeric)"
        function_body = "return query {}".format(query)

        super().__init__(model, function_name, arguments, return_value,
                         function_body)


class AddDateSortFunction(AddFunction):
    reduces_to_sql = True
    reversible = True

    def __init__(self, model, function_name, arguments, query):
        return_value = "table(id int, rank date)"
        function_body = "return query {}".format(query)

        super().__init__(model, function_name, arguments, return_value,
                         function_body)
