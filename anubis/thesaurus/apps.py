from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ThesaurusConfig(AppConfig):
    name = 'anubis.thesaurus'
    label = 'thesaurus'
    verbose_name = _("Thesaurus")

    def ready(self):
        import anubis.thesaurus.signals
