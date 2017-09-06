from django.apps import AppConfig
from django.utils.translation import ugettext as _


class ThesaurusConfig(AppConfig):
    name = 'anubis.thesaurus'
    label = 'thesaurus'
    verbose_name = _("Thesaurus")
