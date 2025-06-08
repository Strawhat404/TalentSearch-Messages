from django.core.files.storage import FileSystemStorage
from whitenoise.storage import CompressedManifestStaticFilesStorage
import os

class WhiteNoiseMediaStorage(FileSystemStorage):
    """
    Custom storage backend that uses WhiteNoise to serve media files in production.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.location = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'media')
        self.base_url = '/media/'
