"""
Signals for fowl app.
Auto-calculate bloodlines when fowl are created/updated.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Gamefowl, FowlBloodline


@receiver(post_save, sender=Gamefowl)
def auto_calculate_bloodlines(sender, instance, created, **kwargs):
    """
    Auto-calculate bloodline percentages when a fowl is created or
    when its sire/dam changes.
    """
    from .services import save_calculated_bloodlines

    # Only auto-calculate if the fowl has parents
    if instance.sire or instance.dam:
        # Check if fowl already has manual bloodlines
        has_manual = instance.bloodline_percentages.filter(
            is_manual_override=True
        ).exists()

        if not has_manual:
            save_calculated_bloodlines(instance)


@receiver(post_save, sender=FowlBloodline)
def propagate_bloodline_changes(sender, instance, created, **kwargs):
    """
    When a fowl's bloodlines are updated, propagate changes to offspring.
    Only triggers for manual overrides or founding birds.
    """
    from .services import propagate_bloodlines_to_offspring

    fowl = instance.fowl

    # Only propagate if this is a manual override or founding bird
    if instance.is_manual_override or (not fowl.sire and not fowl.dam):
        # Check if fowl has offspring before triggering expensive propagation
        if fowl.offspring.exists():
            propagate_bloodlines_to_offspring(fowl)
