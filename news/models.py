from django.db import models

class News(models.Model):
    title = models.CharField(max_length=255, help_text="Enter a concise news title (max 255 characters).")
    date = models.DateField()
    category = models.CharField(max_length=100)
    content = models.Textfield(help_text = "Provide the full news content")
    image = models.URLField(max_length=200)  # Fixed from max_lenght to max_length
    created_at = models.DateTimeField(auto_now_add=True,help_text = "Auto-set creation date")

    def __str__(self):
        return self.title