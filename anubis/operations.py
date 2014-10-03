# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# operations.py - operações de migração customizadas para o Anubis.

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

from django.db.migrations.operations.base import Operation

class LoadExtension(Operation):
	reduces_to_sql = True
	reversible = True

	def __init__(self, name):
		self.name = name

	def state_forwards(self, app_label, state):
		pass

	def database_forwards(self, app_label, schema_editor, from_state, to_state):
		schema_editor.execute("create extension if not exists %s" % self.name)

	def database_backwards(self, app_label, schema_editor, from_state, to_state):
		schema_editor.execute("drop extension %s" % self.name)

	def describe(self):
		return "Creates extension %s" % self.name

class AddCustomIndex(Operation):
	reduces_to_sql = True
	reversible = True

	def __init__(self, model, index_name, sql):
		self.model = model
		self.table_name = self.model._meta.db_table
		self.index_name = "{}_{}".format(self.table_name, index_name)
		self.sql = sql

	def state_forwards(self, app_label, state):
		pass

	def database_forwards(self, app_label, schema_editor, from_state,
			to_state):
		query = """
			create index {index} on {table} using {text};
		"""

		query = query.format(table=self.table_name,
			index=self.index_name, text=self.sql)

		schema_editor.execute(query)

	def database_backwards(self, app_label, schema_editor, from_state,
			to_state):
		query = """
			drop index if exists {index} cascade;
		"""
		query = query.format(index=self.index_name)

		schema_editor.execute(query)

	def describe(self):
		return "Add index {} to table {}".format(self.index_name,
			self.table_name)

class AddCustomViewIndex(AddCustomIndex):
	reduces_to_sql = True
	reversible = True

	def __init__(self, model, view_name, index_name, sql):
		super().__init__(model, index_name, sql)
		self.table_name = "{}_{}".format(self.table_name, view_name)

	def describe(self):
		return "Add index {} to view {}".format(self.index_name,
			self.table_name)



class AddTrigramIndex(AddCustomIndex):
	reduces_to_sql = True
	reversible = True

	def __init__(self, model, field_name):
		index_name = "{}_trgm_index".format(field_name)
		sql = "gist ({} gist_trgm_ops)".format(field_name)

		super().__init__(model, index_name, sql)

	def describe(self):
		return "Add trigram index {} to table {}".format(self.index_name,
			self.table_name)




class AddConstraint(Operation):
	reduces_to_sql = True
	reversible = True

	def __init__(self, model, constraint_name, sql):
		self.model = model
		self.table_name = self.model._meta.db_table
		self.constraint_name = "{}_{}".format(self.table_name, constraint_name)
		self.sql = sql

	def state_forwards(self, app_label, state):
		pass

	def database_forwards(self, app_label, schema_editor, from_state,
			to_state):
		query = """
			alter table if exists \"{table}\"
				add constraint \"{constraint}\" {text};
		"""

		query = query.format(table=self.table_name,
			constraint=self.constraint_name, text=self.sql)

		schema_editor.execute(query)

	def database_backwards(self, app_label, schema_editor, from_state,
			to_state):
		query = """
			alter table if exists \"{table}\"
				drop constraint if exists \"{constraint}\" cascade;
		"""
		query = query.format(table=self.table_name,
			constraint=self.constraint_name)

		schema_editor.execute(query)

	def describe(self):
		return "Add constraint {} to table {}".format(self.constraint_name,
			self.table_name)

class AddCheckConstraint(AddConstraint):
	reduces_to_sql = True
	reversible = True

	def __init__(self, table_name, constraint_name, comparison):
		sql = "check ( {} )".format(comparison)
		super().__init__(table_name, constraint_name, sql)

class AddStartBeforeEndConstraint(AddCheckConstraint):
	reduces_to_sql = True
	reversible = True

	def __init__(self, table_name, lesser="start_date", greater="end_date"):
		super().__init__(table_name, "start_before_end",
				'"{}" < "{}"'.format(lesser, greater))

class AddGistConstraint(AddConstraint):
	reduces_to_sql = True
	reversible = True

	def __init__(self, table_name, constraint_name, expressions,
			condition=None):
		expr = ",".join(["{} with {}".format(expr, oper)
			for expr, oper in expressions])

		if condition is None:
			where = ""
		else:
			where = " where {}".format(condition)

		sql = "exclude using gist ( {} ){};".format(expr, where)

		super().__init__(table_name, constraint_name, sql)

class AddNoDateRangeOverlappingConstraint(AddGistConstraint):
	reduces_to_sql = True
	reversible = True

	def __init__(self, table_name, restraint_field=None,
			start_date="start_date", end_date="end_date", coalesce=True,
			condition=None):

		if coalesce:
			end_date = "coalesce({}, 'infinity'::date)".format(end_date)

		expressions = [("daterange({}, {})".format(start_date, end_date),
			"&&")]

		if restraint_field is not None:
			expressions.insert(0, (restraint_field, "="))

		super().__init__(table_name, "no_overlapping", expressions, condition)


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

		return sql.format \
			( full_name=self.get_full_name()
			, return_value=self.return_value
			, function_body=self.function_body
			)

	def state_forwards(self, app_label, state):
		pass

	def database_forwards(self, app_label, schema_editor, from_state, to_state):
		body = self.get_full_body()
		# print(body)
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

class AddView(Operation):
	reduces_to_sql = True
	reversible = True

	def __init__(self, base_model, name, query):
		self.model = base_model
		self.name = "{}_{}".format(self.model._meta.db_table, name)
		self.query = query

	def state_forwards(self, app_label, state):
		pass

	def database_forwards(self, app_label, schema_editor, from_state, to_state):
		sql = "create or replace view {name} as {query};".format(name=self.name,
			query=self.query)
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

	def database_forwards(self, app_label, schema_editor, from_state, to_state):
		sql = "create materialized view {name} as ({query});" \
			.format(name=self.name, query=self.query)
		schema_editor.execute(sql)

	def database_backwards(self, app_label, schema_editor, from_state,
			to_state):
		sql = "drop materialized view if exists {name};".format(name=self.name)
		schema_editor.execute(sql)

	def describe(self):
		return "Creates materialized view {}.".format(self.name)

class AddTrigger(Operation):
	reduces_to_sql = True
	reversible = True

	class On:
		UPDATE = 1 << 0
		INSERT = 1 << 1
		DELETE = 1 << 2
		ALL = UPDATE | INSERT | DELETE

		_list = \
			[ ("update", UPDATE)
			, ("insert", INSERT)
			, ("delete", DELETE)
			]

	def __init__(self, model, name, commands, after=True, on=On.ALL,
			row_level=False, condition=None):
		self.model = model
		self.table_name = self.model._meta.db_table
		self.name = "{}_{}_trigger".format(self.table_name, name)
		self.function_name = "{}_{}_fn()".format(self.table_name, name)
		self._events = on
		self.commands = commands
		self.when = "after" if after else "before"
		self.row_level = "for each row" if row_level else ""
		self.condition = "" if condition is None else "when ( {} )" \
			.format(condition)

	@property
	def events(self):
		events = [event for event, mask in self.On._list if self._events & mask]

		return " or ".join(events)


	def _sql(self):
		sql = """
			create function {function_name} returns trigger
			language 'plpgsql' as $$
			begin
				{commands}
				return null;
			end
			$$;

			create trigger {name} {when} {events} on "{table}" {row_level} execute procedure {function_name};
		""".format(function_name=self.function_name, commands=self.commands,
			name=self.name, when=self.when, events=self.events,
			table=self.table_name, row_level=self.row_level)

		return sql

	def state_forwards(self, app_label, state):
		pass

	def database_forwards(self, app_label, schema_editor, from_state, to_state):
		schema_editor.execute(self._sql())

	def database_backwards(self, app_label, schema_editor, from_state,
			to_state):
		sql = """
			drop trigger if exists {name} on {table} cascade;
			drop function if exists {function_name};
		""".format(name=self.name, function_name=self.function_name,
			table=self.table_name)

		schema_editor.execute(sql)

	def describe(self):
		return "Creates trigger {} and corresponding function {}." \
			.format(self.name, self.function_name)

class AddTableTrigger(AddTrigger):
	reduces_to_sql = True
	reversible = True

	def __init__(self, table_name, name, commands, after=True,
			on=AddTrigger.On.ALL, row_level=False, condition=None):
		self.model = None
		self.table_name = table_name
		self.name = "{}_{}_trigger".format(self.table_name, name)
		self.function_name = "{}_{}_fn()".format(self.table_name, name)
		self._events = on
		self.commands = commands
		self.when = "after" if after else "before"
		self.row_level = "for each row" if row_level else ""
		self.condition = "" if condition is None else "when ( {} )" \
			.format(condition)


class AddRefreshMaterializedViewTrigger(AddTrigger):
	reduces_to_sql = True
	reversible = True

	def __init__(self, trigger_model, materialized_view_model,
			materialized_view_name):
		view_name = "{}_{}" \
			.format(materialized_view_model._meta.db_table,
				materialized_view_name)

		commands = "refresh materialized view {};".format(view_name)

		# def __init__(self, model, name, commands, after=True, on=On.ALL,
		# 		defer=False, row_level=False, condition=None):
		super().__init__ \
			( trigger_model
			, "refresh_{}".format(view_name)
			, commands
			)

class AddRefreshMaterializedViewTableTrigger(AddTableTrigger):
	reduces_to_sql = True
	reversible = True

	def __init__(self, trigger_table, materialized_view_model,
			materialized_view_name):
		view_name = "{}_{}" \
			.format(materialized_view_model._meta.db_table,
				materialized_view_name)

		commands = "refresh materialized view {};".format(view_name)

		# def __init__(self, model, name, commands, after=True, on=On.ALL,
		# 		defer=False, row_level=False, condition=None):
		super().__init__ \
			( trigger_table
			, "refresh_{}".format(view_name)
			, commands
			)








