
from django.conf.urls import include

from anubis.thesaurus import urls

urls = include(urls)

default_app_config = "anubis.thesaurus.apps.ThesaurusConfig"

__all__ = ['urls', 'default_app_config']
