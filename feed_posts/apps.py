from django.apps import AppConfig

class FeedPostsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'feed_posts'
    verbose_name = 'Feed Posts'

    def ready(self):
        try:
            import feed_posts.signals  # noqa
        except ImportError:
            pass 