# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# url.py - parser de URL em expressão booleana.

# Este arquivo é parte do software Anubis.

# Anubis é um software livre: você pode redistribuí-lo e/ou
# modificá-lo sob os termos da Licença Pública Geral GNU (GNU General Public
# License), tal como é publicada pela Free Software Foundation, na versão 3 da
# licença, ou (sua decisão) qualquer versão posterior.

# Anubis é distribuído na esperança de que seja útil, mas SEM NENHUMA
# GARANTIA; nem mesmo a garantia implícita de VALOR COMERCIAL ou ADEQUAÇÃO
# PARA UM PROPÓSITO EM PARTICULAR. Veja a Licença Pública Geral GNU para
# mais detalhes.

# Você deve ter recebido uma cópia da Licença Pública Geral GNU junto com
# este programa. Se não, consulte <http://www.gnu.org/licenses/>.

import ctypes
import pkg_resources
import json
from threading import Lock

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
			return func(not_expression=expr["expr"].traverse(func),
				inside_type=expr["expr"].type_.__class__)

	class And(Type):
		fields = ("left", "right")

		@staticmethod
		def repr(expr):
			return "({}) AND ({})".format(str(expr["left"]), str(expr["right"]))

		@staticmethod
		def traverse(expr, func):
			return func(and_expression=(expr["left"].traverse(func),
				expr["right"].traverse(func)),
				left_type=expr["left"].type_.__class__,
				right_type=expr["right"].type_.__class__)

	class Or(Type):
		fields = ("left", "right")

		@staticmethod
		def repr(expr):
			return "({}) OR ({})".format(str(expr["left"]), str(expr["right"]))

		@staticmethod
		def traverse(expr, func):
			return func(or_expression=(expr["left"].traverse(func),
				expr["right"].traverse(func)),
				left_type=expr["left"].type_.__class__,
				right_type=expr["right"].type_.__class__)

	types = \
		{ "BooleanExpr": Expr()
		, "Not": Not()
		, "And": And()
		, "Or": Or()
		}

	precedence = \
		[ Expr
		, Not
		, And
		, Or
		]

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

	def __init__(self, url):
		self.url = url

	def build(self):
		url_bytestr = self.url.encode("utf-8")

		with HaskellLibrary(self.parser_lib_path) as parser_lib:
			parser_lib.parseUrl.argtypes = [ctypes.c_char_p]
			parser_lib.parseUrl.restype = ctypes.c_char_p
			json_bytestr = parser_lib.parseUrl(url_bytestr)

		json_str = json_bytestr.decode("utf-8")
		json_obj = json.loads(json_str, object_hook=Boolean.build)

		return json_obj

	@property
	def parser_lib_path(self):
		return pkg_resources.resource_filename("anubis", self.parser_lib_name)

class HaskellLibrary:
	libdl = "libdl.so"
	_locks = {}
	_master_lock = Lock()

	def __init__(self, lib_path):
		self.lib_path = lib_path
		self.library = None

		with self._master_lock:
			if self.lib_path not in self._locks.keys():
				self._locks[self.lib_path] = Lock()

			self.lock = self._locks[self.lib_path]

	def __enter__(self):
		self.lock.acquire()
		self.library = ctypes.cdll.LoadLibrary(self.lib_path)

		self.library.hs_init(0, 0)

		return self.library

	def __exit__(self, type_, value, traceback):
		self.library.hs_exit()
		self._dlclose()

		del self.library
		self.library = None

		self.lock.release()

	def _dlclose(self):
		libdl = ctypes.cdll.LoadLibrary(self.libdl)
		libdl.dlclose.argtypes = [ctypes.c_void_p]
		libdl.dlclose.restype = ctypes.c_int
		libdl.dlclose(self.library._handle)

