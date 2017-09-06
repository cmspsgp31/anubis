""" Thesaurus models.
"""

from datetime import datetime

from django.conf import settings
from django.utils.translation import ugettext as _
from django.db import models
from django.contrib.postgres import fields as postgres
from django.core.exceptions import ValidationError

from anubis.query import ProcedureQuerySet

class TrackCreatorMixin:
    creator = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        blank=False,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Created by")
    )

    created_at = models.DateTimeField(
        blank=False,
        null=False,
        verbose_name=_("Created at"),
        default=lambda : datetime.now()
    )

class TrackModifierMixin:
    modifier = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        blank=False,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Last modified by")
    )

    last_modified_at = models.DateTimeField(
        blank=False,
        null=False,
        verbose_name=_("Last modified at"),
    )

class Thesaurus(models.Model):
    class Meta:
        verbose_name = _("Thesaurus")
        verbose_name_plural = _("Thesauri")

    name = models.TextField(
        verbose_name=_("Name"),
        null=False,
        blank=False
    )

class Node(TrackCreatorMixin, TrackModifierMixin, models.Model):
    class Meta:
        verbose_name = _("Term")
        verbose_name_plural = _("Terms")

    class QuerySet(ProcedureQuerySet):
        pass

    objects = QuerySet.as_manager()

    label = models.TextField(
        verbose_name=_("Term"),
        null=False,
        blank=False,
        unique=True
    )

    children = models.ManyToManyField(
        to="Node",
        through="Edge",
        through_fields=("start_node", "end_node"),
        related_name="parents",
        verbose_name=_("Child terms"),
    )

    thesaurus = models.ForeignKey(
        to="Thesaurus",
        related_name="nodes",
        verbose_name=_("Thesaurus"),
        blank=False,
        null=False
    )

    apps = postgres.ArrayField(
        models.TextField(
            blank=False,
            null=False
        ),
        verbose_name=_("App availability"),
        blank=True,
        null=False,
        help_text=_(("Comma-separated list of apps "
                     "that can use this term.")),
    )



class Edge(TrackCreatorMixin, TrackModifierMixin, models.Model):
    class Meta:
        verbose_name = _("Edge")
        verbose_name_plural = _("Edges")

    start_node = models.ForeignKey(
        to="Node",
        related_name="child_edges",
        blank=False,
        null=False,
        verbose_name=_("Parent term")
    )

    end_node = models.ForeignKey(
        to="Node",
        related_name="parent_edges",
        blank=False,
        null=False,
        verbose_name=_("Child term")
    )

    facet = models.ForeignKey(
        to="FacetIndicator",
        related_name="on_edges",
        blank=True,
        null=True,
        verbose_name=_("Facet indicator"),
        default=None
    )

    def clean_facets(self):
        """ Validate facets to assure the user has only used facets owned
            by the start node in the edge.
        """

        if self.facet is not None and \
                not self.facet.for_node == self.start_node:
            raise ValidationError(_(("You cannot use a facet indicator from "
                                     "the term \"{owner}\" in an edge whose "
                                     "parent is a different term "
                                     "(\"{parent}\")."
                                    ).format(owner=self.facet.for_node.label,
                                             parent=self.start_node.label)
                                   ))

    def clean_thesaurus(self):
        """ Validate that both the start and end nodes belong to the same
            thesaurus.
        """

        if not self.start_node.thesaurus == self.end_node.thesaurus:
            raise ValidationError(_(("Parent term \"{parent}\" and child term "
                                     "\"{child}\" don't belong to the same "
                                     "thesaurus."
                                    ).format(parent=self.start_node.label,
                                             child=self.end_node.label)
                                   ))

    def clean(self):
        """ Performs all validations.
        """
        self.clean_facets()
        self.clean_thesaurus()

        return super().clean()

class FacetIndicator(models.Model):
    class Meta:
        verbose_name = _("Facet Indicator") # rótulo nodal
        verbose_name_plural = _("Facet Indicators")

    label = models.TextField(
        verbose_name=_("Nome"),
        blank=False,
        null=False
    )

    for_node = models.ForeignKey(
        to="Node",
        related_name="facet_indicators",
        blank=False,
        null=False,
        verbose_name=_("Term")
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

    node = models.ForeignKey(
        to="Node",
        related_name="notes",
        verbose_name=_("Term"),
        blank=False,
        null=False
    )
