import ctypes, json

lib = ctypes.cdll.LoadLibrary("libparseurl.so")
lib.parseUrl.restype = ctypes.c_char_p

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
			print(repr(json.loads(json_obj.decode("utf-8"))))
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
