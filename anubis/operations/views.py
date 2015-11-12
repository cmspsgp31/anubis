# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# views.py - operações de migração de views de PostgreSQL.

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
    Operações de migração de views de PostgreSQL.
"""

from django.db.migrations.operations.base import Operation

class AddView(Operation):
    reduces_to_sql = True
    reversible = True

    def __init__(self, base_model, name, query):
        self.model = base_model
        self.name = "{}_{}".format(self.model._meta.db_table, name)
        self.query = query

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, from_state,
                          to_state):
        sql = "create or replace view {name} as {query};" \
              .format(name=self.name, query=self.query)

        schema_editor.execute(sql)

    def database_backwards(self, app_label, schema_editor, from_state,
                           to_state):
        sql = "drop view if exists {name};".format(name=self.name)
        schema_editor.execute(sql)

    def describe(self):
        return "Creates view {}.".format(self.name)


class AddMaterializedView(AddView):
    reduces_to_sql = True
    reversible = True

    def database_forwards(self, app_label, schema_editor, from_state,
                          to_state):
        sql = "create materialized view {name} as ({query});" \
              .format(name=self.name, query=self.query)

        schema_editor.execute(sql)

    def database_backwards(self, app_label, schema_editor, from_state,
                           to_state):
        sql = "drop materialized view if exists {name};".format(name=self.name)
        schema_editor.execute(sql)

    def describe(self):
        return "Creates materialized view {}.".format(self.name)
