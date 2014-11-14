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

		self.es_server.delete(**es_args)

		return retval




class ElasticQuerySet(ProcedureQuerySet):
	def es_query(self, body, save_score=True, save_highlights=True):
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

		print(body)
		es_queryset = scan(es_server, query=body, **path)
		data = {d["_id"]: d for d in es_queryset}

		queryset = self.filter(id__in=data.keys())

		if save_score or save_highlights:
			for element in queryset:
				hit = data[str(element.id)]
				print(hit)
				element._es_score = hit["_score"]
				element._es_highlights = hit["highlight"]

		return queryset
