# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# elastic.py - extensões relativas a ElasticSearch.

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

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from elasticsearch.helpers import scan
from anubis.query import ProcedureQuerySet
from anubis.filters import Filter
from django.conf import settings

class ElasticModelMixin:
	""" O propósito dessa classe é fornecer um backend reserva para um modelo
	já implementado em outro backend. Por exemplo, quando os metadados de um
	modelo estão em SQL, e os dados de pesquisa em texto completo no Elastic.
	Essa classe fornece funções utilitárias para simplificar a transposição de
	dados de um modelo para o outro. Ela NÃO tem o propósito de ser usada como
	um modelo "nativo" de ElasticSearch para Django.

	Exemplo:

	class MyModel(ElasticModelMixin, django.db.models.Model):
		_elastic = {
			"connection": "myconn", # id da conexão em settings.ELASTICSEARCH
			"path": {"index": "people", "doc_type": "person"},
				# índice e doc_type no ElasticSearch
			"fields": ("nome", "idade") # campos do documento
			"highlight": ("nome") # campos a serem destacados no resultado
		}

		primeiro_nome = django.db.models.CharField()
		sobrenome = django.db.models.CharField()
		idade = django.db.models.IntegerField()
			# nome do campo no modelo do Django coincide com nome do campo
			# do documento, então será usado preencher esse dado

		def es_get_field_nome(self):
			# usa essa função para prover o dado para o ElasticSearch
			return self.primeiro_nome + " " + self.sobrenome
	"""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self._es_server = None
		self._es_score = None
		self._es_highlights = None

	@classmethod
	def es_get_server(cls):
		connection_id = cls._elastic["connection"]
		connection_string = settings.ELASTICSEARCH[connection_id]
		return Elasticsearch(connection_string)

	@property
	def es_server(self):
		if self._es_server is None:
			connection_id = self._elastic["connection"]
			connection_string = settings.ELASTICSEARCH[connection_id]
			self._es_server = Elasticsearch(connection_string)

		return self._es_server

	@property
	def es_fields(self):
		return tuple(self._elastic["fields"])

	def es_get_field(self, field):
		if not field in self.es_fields:
			raise KeyError("Undeclared ElasticSearch field - {}.".format(field))

		field_getter_name = "es_get_field_{}".format(field)
		value = None

		if hasattr(self, field_getter_name):
			getter = getattr(self, field_getter_name)

			if callable(getter):
				value = getter()
			else:
				value = getter

		elif field in self._meta.get_all_field_names():
			value = getattr(self, field)

		else:
			msg = "No source found for field {f} - tried {c}.{m}, {c}.{m}() and \
					self._meta.get_all_field_names().".format(f=field,
						c=self.__class__.__name__, m=field_getter_name)

			raise KeyError(msg)

		return value

	def es_retrieve_field(self, field):
		if not field in self.es_fields:
			raise KeyError("Undeclared ElasticSearch field - {}.".format(field))

		doc = self.es_server.get(id=self.id, **self._elastic["path"])

		return doc["_source"][field]




	def save(self, save_es=False, *args, **kwargs):
		retval = super().save(*args, **kwargs)

		if save_es:
			es_args = dict(self._elastic["path"])
			es_args.update( \
				{ "body" : {field: self.es_get_field(field) \
					for field in self.es_fields}
				, "id": self.id
				})

			self.es_server.index(**es_args)

		return retval

	def delete(self, *args, **kwargs):
		_id = self.id
		retval = super().delete(*args, **kwargs)

		es_args = dict(self._elastic["path"])
		es_args["id"] = _id

		try:
			self.es_server.delete(**es_args)
		except NotFoundError:
			pass

		return retval




class ElasticQuerySet(ProcedureQuerySet):
	def es_query(self, body, timeout=None, min_score=None, save_score=True,
			save_highlights=True):
		es_server = self.model.es_get_server()
		path = self.model._elastic["path"]
		body = dict(body)
		should_highlight = "highlight" in self.model._elastic.keys()

		body.setdefault("fields", []).append("_id")

		if should_highlight:
			body["fields"].append("highlight")
			highlights = body.setdefault("highlight", {}) \
				.setdefault("fields", {})

			for field in self.model._elastic["highlight"]:
				highlights.setdefault(field, {})

		if timeout is not None:
			timeout = \
				{ "timeout": timeout
				, "scroll": timeout
				}
		else:
			timeout = {}

		kwargs = { "query": body }

		if min_score is not None:
			kwargs["min_score"] = min_score

		kwargs.update(timeout)
		kwargs.update(path)

		print(kwargs)

		es_queryset = scan(es_server, **kwargs)
		data = {d["_id"]: d for d in es_queryset}

		queryset = self.filter(id__in=data.keys())

		if save_score or save_highlights:
			for element in queryset:
				hit = data[str(element.id)]
				print(hit)
				element._es_score = hit["_score"]
				element._es_highlights = hit["highlight"]

		return queryset


class ElasticFilter(Filter):
	def __init__(self,  es_field_name, **es_kwargs):
		self.kwargs = es_kwargs
		self.field_name = es_field_name

		super().__init__(es_field_name)

	def make_query_body(self, args):
		raise NotImplementedError()

	def make_kwargs(self, args):
		return {}

	def get_server(self, queryset):
		return queryset.model.es_get_server()

	def get_path(self, queryset):
		return queryset.model._elastic["path"]

	def default_kwargs(self):
		return {}

	def default_body(self):
		return \
			{ "fields": ["_id"] #, "highlight"]
			# { "highlight": {"fields": {self.field_name: {}}}
			}

	def should_import_results(self):
		return True

	def import_results(self, obj, hit):
		# obj._es_highlights = hit["highlight"]
		pass

	def _filter_django_queryset(self, queryset, args, es_data):
		return queryset.filter(id__in=es_data.keys())

	def _build_kwargs(self, queryset, args):
		path = self.get_path(queryset)
		request_kwargs = self.make_kwargs(args)
		kwargs = self.default_kwargs()


		kwargs.update(self.kwargs)
		kwargs.update(request_kwargs)
		kwargs.update(path)

		return kwargs

	def filter_queryset(self, queryset, args):
		server = self.get_server(queryset)

		query_body = self.default_body()
		query_body.update(self.make_query_body(args))

		kwargs = self._build_kwargs(queryset, args)
		kwargs["query"] = query_body

		es_queryset = scan(server, **kwargs)
		data = {d["_id"]: d for d in es_queryset}

		queryset = self._filter_django_queryset(queryset, args, data)

		if self.should_import_results():
			for obj in queryset:
				hit = data[str(obj.id)]
				self.import_results(obj, hit)

		return queryset

class ElasticMatchPhraseFilter(ElasticFilter):
	def __init__(self, es_field_name, prefix=False, fuzziness="0",
			has_score=False, **es_kwargs):

		super().__init__(es_field_name, **es_kwargs)

		prefix = prefix or not fuzziness == "0"

		self.field_base = \
			{ "fuzziness": fuzziness
			, "type": "phrase_prefix" if prefix else "phrase"
			}

		if prefix:
			self.field_base["max_expansions"] = 100

		self.has_score = has_score

	def make_query_body(self, args):
		from pprint import pprint

		text = args[0]

		body = { "query": { "match": { self.field_name: self.field_base } } }

		if self.has_score:
			body["min_score"] = float(args[1])

		body["query"]["match"][self.field_name]["query"] = text

		pprint(body)

		return body


class ElasticHasFTSFilter(ElasticFilter):
	def _filter_django_queryset(self, queryset, args, es_data):
		have_empty_field = set(es_data.keys())

		server = self.get_server(queryset)
		kwargs = self._build_kwargs(queryset, [])
		kwargs["query"] = self.default_body()

		have_doc = {int(doc["_id"]) for doc in scan(server, **kwargs)}
		all_docs = set(queryset.model.objects.values_list("id", flat=True))
		have_no_doc = all_docs - have_doc

		fts_missing = have_empty_field | have_no_doc

		return queryset.exclude(id__in=list(fts_missing))

	def should_import_results(self):
		return False

	def make_query_body(self, args):
		return {
			"filter": {
				"not": {
					"range": {
						self.field_name: {}
					}
				}
			}
		}
