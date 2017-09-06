
from django.conf.urls import include

from anubis.thesaurus import urls

urls = include(urls)

__all__ = ['urls']
