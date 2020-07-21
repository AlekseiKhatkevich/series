from django.apps import AppConfig


class AdministrationConfig(AppConfig):
    name = 'administration'

    def ready(self):
        import administration.tasks
        import series.lookups_and_transforms
