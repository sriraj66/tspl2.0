from django.apps import AppConfig
class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    def ready(self):
        import atexit
        from .task import email_executor, csv_executor
        atexit.register(lambda: email_executor.shutdown(wait=True))
        atexit.register(lambda: csv_executor.shutdown(wait=True))
        