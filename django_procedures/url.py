# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# url.py - parser de URL em expressão booleana.

# Este arquivo é parte do software django-procedures.

# django-procedures é um software livre: você pode redistribuí-lo e/ou
# modificá-lo sob os termos da Licença Pública Geral GNU (GNU General Public
# License), # tal como é publicada pela Free Software Foundation, na versão 3 da
# licença, ou (sua decisão) qualquer versão posterior.

# django-procedures é distribuído na esperança de que seja útil, mas SEM NENHUMA
# GARANTIA; nem mesmo a garantia implícita de VALOR COMERCIAL ou ADEQUAÇÃO
# PARA UM PROPÓSITO EM PARTICULAR. Veja a Licença Pública Geral GNU para
# mais detalhes.

# Você deve ter recebido uma cópia da Licença Pública Geral GNU junto com
# este programa. Se não, consulte <http://www.gnu.org/licenses/>.

import ctypes
import pkg_resources
import json

class Boolean:
	class Type:
		fields = ()

		@staticmethod
		def set_contents(expr, dictionary):
			expr.contents = dictionary

	class Expr(Type):
		fields = ("field", "args")

		@staticmethod
		def repr(expr):
			return "{}: {}".format(repr(expr["field"]), expr["args"])

		@staticmethod
		def set_contents(expr, dictionary):
			expr.contents = dictionary["contents"]

		@staticmethod
		def traverse(expr, func):
			return func(base_expression=expr)

	class Not(Type):
		fields = ("expr",)

		@staticmethod
		def repr(expr):
			return "NOT ({})".format(str(expr["expr"]))

		@staticmethod
		def set_contents(expr, dictionary):
			expr.contents = dict(expr=dictionary["contents"])

		@staticmethod
		def traverse(expr, func):
			return func(not_expression=expr["expr"].traverse(func))

	class And(Type):
		fields = ("left", "right")

		@staticmethod
		def repr(expr):
			return "({}) AND ({})".format(str(expr["left"]), str(expr["right"]))

		@staticmethod
		def traverse(expr, func):
			return func(and_expression=(expr["left"].traverse(func),
				expr["right"].traverse(func)))

	class Or(Type):
		fields = ("left", "right")

		@staticmethod
		def repr(expr):
			return "({}) OR ({})".format(str(expr["left"]), str(expr["right"]))

		@staticmethod
		def traverse(expr, func):
			return func(or_expression=(expr["left"].traverse(func),
				expr["right"].traverse(func)))

	types = \
		{ "BooleanExpr": Expr()
		, "Not": Not()
		, "And": And()
		, "Or": Or()
		}

	def __init__(self, contents, type_):
		assert isinstance(type_, self.Type)

		self.type_ = type_
		self.type_.set_contents(self, contents)

	@classmethod
	def build(cls, dictionary):
		if "tag" in dictionary.keys():
			if dictionary["tag"] in cls.types.keys():
				return Boolean(dictionary, cls.types[dictionary["tag"]])
			else:
				raise ValueError(dictionary["contents"])

		return dictionary

	def keys(self):
		return self.type_.fields

	def traverse(self, func):
		return self.type_.traverse(self, func)

	def __getitem__(self, key):
		return self.contents[key]

	def __str__(self):
		return self.type_.repr(self)

	def __repr__(self):
		return str(self)

class BooleanBuilder:
	parser_lib_name = "libParseUrl.so"
	_parser_lib = None

	def __init__(self, url):
		self.url = url

	def build(self):
		url_bytestr = self.url.encode("utf-8")
		json_bytestr = self.parser_lib.parseUrl(url_bytestr)
		json_str = json_bytestr.decode("utf-8")
		json_obj = json.loads(json_str, object_hook=Boolean.build)

		return json_obj

	@property
	def parser_lib(self):
		if BooleanBuilder._parser_lib is None:
			lib_file = pkg_resources.resource_filename("django_procedures",
				self.parser_lib_name)
			BooleanBuilder._parser_lib = ctypes.cdll.LoadLibrary(lib_file)
			BooleanBuilder._parser_lib.hs_init(0, 0)
			BooleanBuilder._parser_lib.parseUrl.restype = ctypes.c_char_p

		return BooleanBuilder._parser_lib

def close_lib(lib):
	# On Windows: ctypes.windll.kernel32.FreeLibrary(lib._handle)
	libdl = ctypes.cdll.LoadLibrary("libdl.so")
	hndl = lib._handle
	libdl.dlclose(hndl)

def build_boolean(url):
	shared_lib_file = pkg_resources.resource_filename("django_procedures",
		"libParseUrl.so")
	shared_lib = ctypes.cdll.LoadLibrary(shared_lib_file)

	shared_lib.hs_init(0, 0)
	shared_lib.parseUrl.restype = ctypes.c_char_p

	try:
		json_bytestr = shared_lib.parseUrl(url.encode("utf-8"))
	finally:
		shared_lib.hs_exit()
		close_lib(shared_lib)
		# É necessário fechar completamente a DLL para que o runtime do Haskell
		# seja completamente fechado; caso contrário, o Python segfaulta quando
		# tentando reutilizar a biblioteca.
		# del shared_lib
		# print("deleted")

	json_str = json_bytestr.decode("utf-8")
	json_obj = json.loads(json_str, object_hook=Boolean.build)

	return json_obj
