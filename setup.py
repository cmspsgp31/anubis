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
        proc.communicate(timeout=7200)
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

class CompileHaskellMixin:
    def initialize_options(self):
        self.force_parselib = False

        super().initialize_options()

    def compile_url_parser(self, package_dir, clean_beforehand):
        working = os.path.join(package_dir, "parseurl")

        if clean_beforehand:
            shell("stack clean", cwd=working)

        shell("stack install", cwd=working)

    def run(self):
        super().run()

        target_path = self.install_lib if self.install_lib is not None \
            else os.path.abspath(self.setup_path)

        package_dir = os.path.join(target_path, "anubis")
        final_product = os.path.join(package_dir, "libParseUrl.so")

        final_product_exists = os.path.isfile(final_product)

        should_compile = not final_product_exists or self.force_parselib

        if should_compile:
            self.compile_url_parser(package_dir, final_product_exists)

class CompileFrontendMixin:
    def initialize_options(self):
        self.force_frontend = False

        super().initialize_options()

    def compile_frontend(self, package_dir):
        working = os.path.join(package_dir, "frontend")

        env = dict(os.environ, NODE_ENV=self.frontend_env)

        if shutil.which("yarn") is not None:
            shell("yarn", cwd=working)
        else:
            shell("npm install", cwd=working)

        shell("node_modules/.bin/webpack", cwd=working, env=env)

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
    version="1.0a10",
    packages=[
        "anubis",
        "anubis.app",
        "anubis.app.management",
        "anubis.app.management.commands",
        "anubis.views",
        "anubis.operations",
    ],
    install_requires=[
        "Django >=1.11, <2",
        "djangorestframework",
        "psycopg2-binary"],
    extras_require={
        'caching': ['redis', 'django-redis']
    },
    package_data={
        'anubis': [
            'frontend/webpack.config.js',
            'frontend/package.json',
            'frontend/src/*.js',
            'frontend/src/reducers/*.js',
            'frontend/src/components/*.js',
            'frontend/src/components/TokenField/*.js',
            'parseurl/LICENSE',
            'parseurl/stack.yaml',
            'parseurl/parseurl.cabal',
            'parseurl/Setup.hs',
            'parseurl/src/*.hs',
        ],
        'anubis.app': [
            'static/anubis/.gitignore',
            'templates/*.jsx']},
    cmdclass={
        'install': InstallAnubis,
        'develop': DevelopAnubis
    })
