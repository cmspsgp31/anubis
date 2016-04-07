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


import subprocess
import os
import shutil
import sys
import json
import glob

from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop


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

def find_ghc_runtime():
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

    file_name = "HSrts-ghc{}".format(version)

    path_options = glob.glob(os.path.join(ghc_libraries, "rts*"))

    # extra_lib_path = None

    extra_lib_path = path_options[0] + "/"

    # for path in path_options:
    #     full_name = "lib{}.so".format(file_name)

    #     if os.path.isfile(os.path.join(path, file_name)):
    #         extra_lib_path = path

    #         if not extra_lib_path.endswith("/"):
    #             extra_lib_path += "/"

    #         break

    if extra_lib_path is None:
        raise EnvironmentError("Couldn't find GHC runtime to link against.")

    return (extra_lib_path, file_name)

class CompileHaskellMixin:
    def initialize_options(self):
        self.force_parselib = False

        super().initialize_options()

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

        shutil.copy(src, dst)


    def make_cabal_file(self, package_dir):
        working = os.path.join(package_dir, "parseurl")
        template_path = os.path.join(working, "parseurl.cabal.template")
        cabal_path = os.path.join(working, "parseurl.cabal")
        extra_lib_path, library_path = find_ghc_runtime()

        with open(template_path, "r") as template_fd:
            template_body = template_fd.read()

        with open(cabal_path, "w") as cabal_fd:
            contents = template_body.format(library_path=library_path,
                                            extra_lib_path=extra_lib_path)
            cabal_fd.write(contents)


    def run(self):
        super().run()

        target_path = self.install_lib if self.install_lib is not None \
            else os.path.abspath(self.setup_path)

        package_dir = os.path.join(target_path, "anubis")
        final_product = os.path.join(package_dir, "libParseUrl.so")

        should_compile = not os.path.isfile(final_product) or \
            self.force_parselib

        if should_compile:
            self.compile_url_parser(package_dir)

class CompileFrontendMixin:
    def initialize_options(self):
        self.force_frontend = False

        super().initialize_options()

    def compile_frontend(self, package_dir):
        working = os.path.join(package_dir, "frontend")

        jspm_cmd = ("node_modules/.bin/jspm "
                    "bundle-sfx main build/"
                    "anubis.js {}").format(self.frontend_options)

        shell("npm install", cwd=working)
        shell(jspm_cmd, cwd=working)

        src = os.path.join(working, "build", "anubis.js")
        dst = os.path.join(package_dir, "app", "static", "anubis",
                           "anubis.js")

        shutil.copy(src, dst)

    def run(self):
        super().run()

        target_path = self.install_lib if self.install_lib is not None \
            else os.path.abspath(self.setup_path)

        package_dir = os.path.join(target_path, "anubis")
        final_product = os.path.join(package_dir, "app", "static", "anubis",
                                     "anubis.js")

        should_compile = not os.path.isfile(final_product) or \
            self.force_frontend

        if should_compile:
            self.compile_frontend(package_dir)


class InstallAnubis(CompileFrontendMixin, CompileHaskellMixin, install):
    frontend_options = "--minify --skip-source-maps"

class DevelopAnubis(CompileFrontendMixin, CompileHaskellMixin, develop):
    frontend_options = ""

    user_options = develop.user_options + [
        ("force-frontend", None, "Forces rebuilding the frontend application."),
        ("force-parselib", None, "Forces rebuilding the parser library."),
    ]

    boolean_options = develop.boolean_options + ['force-frontend',
                                                 'force-parselib']

setup(
    name="anubis",
    version="1.0a4",
    packages=[
        "anubis",
        "anubis.app",
        "anubis.views",
        "anubis.operations"],
    install_requires=[
        "Django >=1.8, <1.9",
        "djangorestframework <3",
        "psycopg2"],
    extras_require={
        'caching': ['redis']
    },
    package_data={
        'anubis': [
            'frontend/config.js',
            'frontend/package.json',
            'frontend/src/*.js',
            'frontend/src/reducers/*.js',
            'frontend/src/components/*.js',
            'frontend/src/components/TokenField/*.js',
            'frontend/components/**/*.js',
            'parseurl/*.hs',
            'parseurl/*.template',
            'parseurl/LICENSE'],
        'anubis.app': [
            'static/anubis/.gitignore',
            'templates/*.js']},
    cmdclass={
        'install': InstallAnubis,
        'develop': DevelopAnubis
    })
