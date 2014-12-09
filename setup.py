# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# setup.py - descrição do procedimento de instalação

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


from setuptools import setup
from setuptools.command.install import install as install_

import subprocess, os, shutil, sys

def shell(*args, **kwargs):
	kwargs.update(stdout=sys.stdout, stderr=sys.stderr, shell=True,
		close_fds=False)
	proc = subprocess.Popen(*args, **kwargs)
	try:
		proc.communicate(timeout=600)
	except:
		print("Timeout expired!")
		proc.kill()

class install(install_):
	def run(self):
		install_.run(self)
		package = os.path.join(self.install_lib, "anubis")
		working = os.path.join(package, "parseurl")
		shell("cabal sandbox init", cwd=working)
		shell("cabal update", cwd=working)
		shell("cabal install --dependencies-only --enable-shared", cwd=working)
		shell("cabal configure --enable-shared", cwd=working)
		shell("cabal install", cwd=working)
		src = os.path.join(working, ".cabal-sandbox", "bin",
			"libParseUrl.so")
		dst = os.path.join(package, "libParseUrl.so")
		print(src, dst)
		shutil.copy(src, dst)


setup \
	( name="anubis"
	, version="0.1"
	, packages=["anubis", "anubis.app", "anubis.app.templatetags"]
	, install_requires= ["Django", "djangorestframework", "psycopg2"]
	, package_data= \
		{ 'anubis':
			[ 'parseurl/*.hs'
			, 'parseurl/*.cabal'
			, 'parseurl/LICENSE'
			]
		, 'anubis.app': \
			[ 'frontend/*.coffee'
			, 'frontend/Cakefile'
			, 'frontend/build/anubis.build.js'
			, 'static/anubis/anubis.css'
			, 'templates/*.html'
			]
		}
	, cmdclass={'install': install}
	)
