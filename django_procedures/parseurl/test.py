import ctypes, json

lib = ctypes.cdll.LoadLibrary("libParseUrl.so")
lib.parseUrl.restype = ctypes.c_char_p

class Expr(object):
	def __init__(self, field, args):
		self.field = field
		self.args = args

	def __str__(self):
		return "{}: {}".format(*map(repr, [self.field, self.args]))

class Not(Expr):
	def __init__(self, expr):
		self.expr = expr

	def __str__(self):
		return "NOT ({})".format(str(self.expr))

class Or(Expr):
	def __init__(self, left, right):
		self.left = left
		self.right = right

	def __str__(self):
		return "({}) OR ({})".format(*map(str, [self.left, self.right]))

class And(Expr):
	def __init__(self, left, right):
		self.left = left
		self.right = right

	def __str__(self):
		return "({}) AND ({})".format(*map(str, [self.left, self.right]))

def hook(dct):
	if "tag" in dct.keys():
		if dct["tag"] == "BooleanExpr":
			return Expr(**dct["contents"])
		elif dct["tag"] == "Not":
			return Not(dct["contents"])
		elif dct["tag"] == "And":
			return And(dct["left"], dct["right"])
		elif dct["tag"] == "Or":
			return Or(dct["left"], dct["right"])
		else:
			raise ValueError(dct["contents"])

	return dct

class haskmod:
	def __init__(self, mod):
		self._mod = mod
	def __enter__(self):
		self._mod.hs_init(0,0)
		return self
	def __exit__(self, type_, value, traceback):
		self._mod.hs_exit()

	def __getattribute__(self, name):
		if name.startswith("_"):
			return super().__getattribute__(name)

		def wrapper(s):
			print(s)
			json_obj = getattr(self._mod, name)(s.encode("utf-8"))
			print(json.loads(json_obj.decode("utf-8"), object_hook=hook))
			print()

		return wrapper

if __name__ == "__main__":
	with haskmod(lib) as lib:
		lib.parseUrl("k,v")
		lib.parseUrl("k1,v1/k2,v2")
		lib.parseUrl("k1,v1+k2,v2")
		lib.parseUrl("k1,v1/k2,v2/k3,v3")
		lib.parseUrl("k1,v1+k2,v2+k3,v3")
		lib.parseUrl("k1,v1/k2,v2+k3,v3")
		lib.parseUrl("k1,v1+k2,v2/k3,v3")
		lib.parseUrl("(k1,v1+k2,v2)/k3,v3")
		lib.parseUrl("!(k1,v1+k2,v2)/k3,v3")
		lib.parseUrl("(!k1,v1+k2,v2)/k3,v3")
		lib.parseUrl("(k1,v1+k2,v2)/!k3,v3")
		lib.parseUrl("(k1,v1+k2,\"!+/1?$$$\"//!_1-\")/!k3,v3")
		lib.parseUrl("k1,v1 k2,v2")
		lib.parseUrl("k1,v1 k2,v2/k3,v3")
		lib.parseUrl("k1,v1 k2,v2/(k3,v3)")
		lib.parseUrl("k1,v1 k2,v2/!(k3,v3)")
		lib.parseUrl("k1,\"longo argumento 1\"      k2,\"longo argumento 2\"")
		lib.parseUrl("k1,\"longo argumento 1\"      !k2,\"longo argumento 2\"")
		lib.parseUrl("asdfasdfasd")
