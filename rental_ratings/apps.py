from django.apps import AppConfig


class RentalRatingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rental_ratings"

    def ready(self):
        import rental_ratings.signals
