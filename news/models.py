from django.db import models

class News(models.Model):
    title = models.CharField(max_length=255)
    date = models.DateField()
    category = models.CharField(max_length=100)
    image = models.URLField(max_length=200)  # Fixed from max_lenght to max_length
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title