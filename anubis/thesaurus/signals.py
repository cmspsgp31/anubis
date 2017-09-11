from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from anubis.thesaurus import models

@receiver(post_save, sender=models.Correlation)
def add_symm_correlation(instance, **kwargs):
    reciprocal = {
        "from_node": instance.to_node,
        "to_node": instance.from_node,
        "dimension": instance.dimension,
        "defaults": {
            "last_modified_by": instance.last_modified_by,
            "last_modified_at": instance.last_modified_at,
            "created_by": instance.created_by,
            "created_at": instance.created_at,
        }
    }

    models.Correlation.objects.get_or_create(**reciprocal)

    forward = models.Correlation.objects \
        .filter(from_node=instance.from_node, dimension=instance.dimension) \
        .values_list('to_node', flat=True)

    reverse = models.Correlation.objects \
        .filter(to_node=instance.from_node, dimension=instance.dimension) \
        .values_list('from_node', flat=True)

    diff = set(reverse).difference(set(forward))

    models.Correlation.objects.filter(
        from_node__in=diff,
        to_node=instance.from_node,
        dimension=instance.dimension
    ).delete()

@receiver(post_delete, sender=models.Correlation)
def remove_symm_correlation(instance, **kwargs):
    models.Correlation.objects.filter(
        from_node=instance.to_node,
        to_node=instance.from_node,
        dimension=instance.dimension
    ).delete()
