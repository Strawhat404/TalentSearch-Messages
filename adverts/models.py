from django.db import models
import uuid
# Create your models here.
class Advert(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.URLField(max_length=255)
    title = models.CharField(max_length=255)
    video = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title