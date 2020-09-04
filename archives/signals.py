from django.db.models.base import ModelBase
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.search import SearchVector

from archives.models import Subtitles


@receiver(post_save, sender=Subtitles)
def generate_lexemes(sender: ModelBase, instance: Subtitles, **kwargs) -> None:
    """
    Fills field 'full_text' of model 'Subtitles' with lexemes.
    """
    config = 'simple'

    if instance.full_text is None:
        language_code = instance.language
        language_full_name = instance.get_language_display().lower()

        try:
            config = sender.objects.analyzers_preferences[language_code]
        except KeyError:
            if language_full_name in sender.objects.list_of_analyzers:
                config = language_full_name

        sender.objects.filter(pk=instance.pk).update(
            full_text=SearchVector(F('text'), config=config)
        )
