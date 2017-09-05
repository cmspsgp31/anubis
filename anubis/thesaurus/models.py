""" Thesaurus models.
"""

from django.utils.translation import ugettext as _
from django.db import models

class Term(models.Model):
    class Meta:
        verbose_name = _("Term")
        verbose_name_plural = _("Terms")

    label = models.TextField(
        verbose_name=_("Term"),
        null=False,
        blank=False,
        unique=True
    )

    children = models.ManyToManyField(
        to="Term",
        through="Edge",
        related_name="parents",
        verbose_name=_("Child terms"),
    )


class Edge(models.Model):
    class Meta:
        verbose_name = _("Edge")
        verbose_name_plural = _("Edges")

    parent_term = models.ForeignKey(
        to="Term"
    )

    child_term = models.ForeignKey(
        to="Term"
    )

    facet = models.ForeignKey(
        to="FacetIndicator"
    )

    def clean(self):
        """ Validate facets to assure the user has only used facets owned
            by the parent term in the edge.
        """
        return super().clean()

class FacetIndicator(models.Model):
    class Meta:
        verbose_name = _("Facet Indicator") # rótulo nodal
        verbose_name_plural = _("Facet Indicators")

    for_term = models.ForeignKey(
        to="Term"
    )


class Note(models.Model):
    class Meta:
        verbose_name = _("Note")
        verbose_name_plural = _("Notes")

    title = models.TextField(
        verbose_name=_("Note title"),
        blank=True,
        null=False
    )

    contents = models.TextField(
        verbose_name=_("Note contents"),
        blank=False,
        null=False
    )

    term = models.ForeignKey(
        to="Term",
        related_name="notes",
        verbose_name=_("Term")
    )
