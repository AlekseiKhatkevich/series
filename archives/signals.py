from django.contrib.postgres.search import SearchVector
from django.db.models import F, Func, Value
from django.db.models.base import ModelBase
from django.db.models.signals import post_save
from django.dispatch import receiver

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

        #  Converts  times like 00:00:13,320 to 000013320 . This is needed to avoid FTS parsing it to a bunch
        #  of plain integers. Update is used in order to avoid recursion in post_save.
        #  re.sub(r'(\d\d):(\d\d):(\d\d),(\d\d\d)', r'\1\2\3\4', text) - an alternative pure python implementation.
        sender.objects.filter(pk=instance.pk).update(
            full_text=SearchVector(
                Func(
                    F('text'),
                    Value(r'(\d\d):(\d\d):(\d\d),(\d\d\d)'),
                    Value(r'\1\2\3\4'),
                    Value(r'g'),
                    function='regexp_replace',
                    arity=4,
                ),
                config=config,
            ))
