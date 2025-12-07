from django.apps import AppConfig




class BaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'base'

    def ready(self):
        from base.tasks import fetch_news_task
        # Run every 1 hour
        fetch_news_task(repeat=3600)
