# Copyright © 2014-16, Ugo Pozo
#             2014-16, Câmara Municipal de São Paulo

# setup.py - installation procedure

# This file is part of Anubis.

# Anubis is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Anubis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

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

        env = dict(os.environ, NODE_ENV=self.frontend_env)

        shell("npm install", cwd=working)
        shell("node_modules/.bin/webpack", cwd=working, env=env)

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
    frontend_env = "production"

class DevelopAnubis(CompileFrontendMixin, CompileHaskellMixin, develop):
    frontend_env = "development"

    user_options = develop.user_options + [
        ("force-frontend", None, "Forces rebuilding the frontend application."),
        ("force-parselib", None, "Forces rebuilding the parser library."),
    ]

    boolean_options = develop.boolean_options + ['force-frontend',
                                                 'force-parselib']

setup(
    name="anubis",
    version="1.0a5",
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
            'frontend/webpack.config.js',
            'frontend/package.json',
            'frontend/src/*.js',
            'frontend/src/reducers/*.js',
            'frontend/src/components/*.js',
            'frontend/src/components/TokenField/*.js',
            'parseurl/*.hs',
            'parseurl/*.template',
            'parseurl/LICENSE'],
        'anubis.app': [
            'static/anubis/.gitignore',
            'templates/*.jsx']},
    cmdclass={
        'install': InstallAnubis,
        'develop': DevelopAnubis
    })
