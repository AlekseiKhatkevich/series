from django.apps import AppConfig


class ArchivesConfig(AppConfig):
    name = 'archives'

    def ready(self):
        import archives.tasks
        import series.lookups_and_transforms
        import archives.signals

