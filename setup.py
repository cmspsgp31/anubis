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
from setuptools.command.install import install

import subprocess
import os
import shutil
import sys
import json


def shell(*args, **kwargs):
    kwargs.update(stdout=sys.stdout, stderr=sys.stderr, shell=True,
                  close_fds=False)
    proc = subprocess.Popen(*args, **kwargs)
    try:
        proc.communicate(timeout=600)
    except subprocess.TimeoutExpired:
        print("Timeout expired!")
        proc.kill()


def shell_output(*args, **kwargs):
    kwargs.update(stdout=subprocess.PIPE, shell=True)

    proc = subprocess.Popen(*args, **kwargs)
    try:
        out, _ = proc.communicate(timeout=600)
    except subprocess.TimeoutExpired:
        print("Timeout expired!")
        proc.kill()
        return None
    else:
        return out


class InstallAnubis(install):

    def compile_url_parser(self, package_dir):
        working = os.path.join(package_dir, "parseurl")

        self.make_cabal_file(package_dir)

        shell("cabal sandbox init", cwd=working)
        shell("cabal update", cwd=working)
        shell("cabal install --dependencies-only --enable-shared", cwd=working)
        shell("cabal configure --enable-shared", cwd=working)
        shell("cabal install", cwd=working)

        src = os.path.join(working, ".cabal-sandbox", "bin",
                           "libParseUrl.so")
        dst = os.path.join(package_dir, "libParseUrl.so")

        print(src, dst)
        shutil.copy(src, dst)

    def find_hs_rts(self):
        bin_info = shell_output("ghc --info")

        info = json.loads(bin_info
                          .strip()
                          .decode("utf-8")
                          .replace("(", "[")
                          .replace(")", "]"))

        ghc_libraries = dict(info)["LibDir"].strip("\n")

        version = shell_output("ghc --version") \
                  .decode("utf-8") \
                  .split(" ")[-1] \
                  .strip("\n")

        file_name = "libHSrts-ghc{}.so".format(version)

        return os.path.join(ghc_libraries, "rts", file_name)

    def make_cabal_file(self, package_dir):
        working = os.path.join(package_dir, "parseurl")
        template_path = os.path.join(working, "parseurl.cabal.template")
        cabal_path = os.path.join(working, "parseurl.cabal")
        library_path = self.find_hs_rts()

        with open(template_path, "r") as template_fd:
            template_body = template_fd.read()

        with open(cabal_path, "w") as cabal_fd:
            contents = template_body.format(library_path=library_path)
            cabal_fd.write(contents)

    def compile_frontend(self, package_dir):
        working = os.path.join(package_dir, "app", "frontend")

        shell("cake debug", cwd=working)

    def run(self):
        super().run()

        package_dir = os.path.join(self.install_lib, "anubis")

        self.compile_url_parser(package_dir)
        self.compile_frontend(package_dir)


setup(
    name="anubis",
    version="0.1",
    packages=[
        "anubis",
        "anubis.app",
        "anubis.app.templatetags"],
    install_requires=[
        "Django<1.8",
        "djangorestframework<3",
        "psycopg2"],
    package_data={
        'anubis': [
            'parseurl/*.hs',
            'parseurl/*.template',
            'parseurl/LICENSE'],
        'anubis.app': [
            'frontend/*.coffee',
            'frontend/Cakefile',
            'frontend/build/anubis.build.js',
            'static/anubis/anubis.css',
            'templates/*.html']},
    cmdclass={
        'install': InstallAnubis})
