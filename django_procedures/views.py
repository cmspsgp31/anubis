# Copyright (C) 2014, Ugo Pozo
#               2014, Câmara Municipal de São Paulo

# views.py - views do django-procedures

# Este arquivo é parte do software django-procedures.

# django-procedures é um software livre: você pode redistribuí-lo e/ou modificá-lo
# sob os termos da Licença Pública Geral GNU (GNU General Public License),
# tal como é publicada pela Free Software Foundation, na versão 3 da
# licença, ou (sua decisão) qualquer versão posterior.

# django-procedures é distribuído na esperança de que seja útil, mas SEM NENHUMA
# GARANTIA; nem mesmo a garantia implícita de VALOR COMERCIAL ou ADEQUAÇÃO
# PARA UM PROPÓSITO EM PARTICULAR. Veja a Licença Pública Geral GNU para
# mais detalhes.

# Você deve ter recebido uma cópia da Licença Pública Geral GNU junto com
# este programa. Se não, consulte <http://www.gnu.org/licenses/>.

from rest_framework.views import APIView
from django.template.loaders.app_directories import Loader
from rest_framework.exceptions import NotAcceptable
from rest_framework.response import Response

class TemplateRetrieverView(APIView):
	allowed_views = {}
	allowed_templates = []
	allowed_methods = {}

	def get(self, request, templates):
		templates = templates.split(",")
		response = {}

		for template in templates:
			try:
				view_name, view_method = template.split(".")
			except ValueError:
				if not template in self.allowed_templates:
					raise NotAcceptable("Template: {}".format(template))

				loader = Loader()
				name = "{}.html".format(template)
				template_body = loader.load_template_source(name)[0]

				response[template] = template_body
			else:
				if view_name not in self.allowed_views.keys():
					raise NotAcceptable("View: {}".format(view_name))

				view = self.allowed_views[view_name]

				if view_name in self.allowed_methods.keys() and \
						view_method not in self.allowed_methods[view_name]:
					raise NotAcceptable("Method: {}.{}".format(view_name,
						view_method))

				views = getattr(view, view_method)()

				response.update({"{}.{}".format(view_name, name): template_body\
					for name, template_body in views.items()})

		return Response(response)



