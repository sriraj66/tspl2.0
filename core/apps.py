from django.apps import AppConfig
from .task import email_executor

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    def ready(self):
        import atexit
        atexit.register(lambda: email_executor.shutdown(wait=True))
        