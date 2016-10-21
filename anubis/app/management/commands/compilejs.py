# Copyright © 2016, Ugo Pozo
#             2016, Câmara Municipal de São Paulo

# compilejs.py - an admin command to compile custom JS.

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

"""
This module defines the compilejs command, which should be used to compile JSX
and/or ES6 JavaScript views written by a library user into ES5 JavaScript.
"""

import os
import subprocess
import sys

import anubis

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.template.loaders.app_directories import get_app_template_dirs

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


class Command(BaseCommand):
    """The command that compiles JSX/ES6 into ES5 JavaScript, using Node and
    Babel as a backend.
    """

    help = ("The command that compiles JSX/ES6 into ES5 JavaScript, using Node"
            " and Babel as a backend.")

    default_extensions = ['.jsx', '.es6']

    presets = ['es2015',
               'react',
               'stage-0']

    plugins = ['transform-decorators-legacy']

    def handle(self, *args, **options):
        directories = set([dir_ for dir_ in get_app_template_dirs('templates')])

        if len(settings.TEMPLATES) > 0:
            if 'DIRS' in settings.TEMPLATES[0].keys():
                direectories = directories.union(set(
                    settings.TEMPLATES[0]['DIRS']))

        extensions = self.default_extensions

        if hasattr(settings, 'ANUBIS_JS_EXTENSIONS'):
            extensions = settings.ANUBIS_JS_EXTENSIONS

        jsx_files = [os.path.join(dir_, fname)
                     for dir_ in directories
                     for _, __, fnames in os.walk(dir_)
                     for fname in fnames
                     if os.path.splitext(fname)[1] in extensions]

        working_path = os.path.join(*[os.path.dirname(anubis.__file__),
                                      "frontend"])

        node_path = os.path.join(working_path, "node_modules")

        presets = ",".join(self.presets)
        plugins = ",".join(self.plugins)
        options = "-s inline" if settings.DEBUG else "--minified"

        for source in jsx_files:
            root, _ = os.path.splitext(source)
            target = root + ".js"

            self.stdout.write("{} -> {}".format(source, target))

            shell('pwd', cwd=working_path)

            shell(("./node_modules/.bin/babel -o {} --presets {} --plugins {} "
                   "--compact true {} {}").format(target, presets, plugins,
                                                  options, source),
                  cwd=working_path,
                  env=dict(os.environ, NODE_PATH=node_path))


