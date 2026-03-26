from django.apps import AppConfig


class FowlConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.fowl'
    verbose_name = 'Gamefowl Management'

    def ready(self):
        import apps.fowl.signals  # noqa
