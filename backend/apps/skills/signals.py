from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import WorkerSkill, WorkerSkillHistory


@receiver(pre_save, sender=WorkerSkill)
def capture_previous_skill_values(sender, instance, **kwargs):
    if instance.pk:
        instance._previous_skill_values = sender.objects.filter(pk=instance.pk).values_list(
            "proficiency", "years_experience"
        ).first()
    else:
        instance._previous_skill_values = None


@receiver(post_save, sender=WorkerSkill)
def record_skill_snapshot(sender, instance, created, **kwargs):
    previous = getattr(instance, "_previous_skill_values", None)
    current = (instance.proficiency, instance.years_experience)
    if created or previous != current:
        WorkerSkillHistory.objects.create(
            worker=instance.worker,
            skill=instance.skill,
            proficiency=instance.proficiency,
            years_experience=instance.years_experience,
        )
