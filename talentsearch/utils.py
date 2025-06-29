"""
Utility functions for Cloudinary image and video handling.
"""

import cloudinary
import cloudinary.uploader
import cloudinary.api
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import logging

logger = logging.getLogger(__name__)

def get_cloudinary_url(public_id, transformation=None, resource_type='image'):
    """
    Get a Cloudinary URL with optional transformations.
    
    Args:
        public_id (str): The public ID of the resource
        transformation (dict): Optional transformation parameters
        resource_type (str): Type of resource ('image' or 'video')
    
    Returns:
        str: The Cloudinary URL
    """
    try:
        if not hasattr(settings, 'CLOUDINARY_STORAGE'):
            logger.warning("Cloudinary not configured")
            return None
            
        cloud_name = settings.CLOUDINARY_STORAGE.get('CLOUD_NAME')
        if not cloud_name:
            logger.warning("Cloudinary cloud name not configured")
            return None
            
        # Build the URL
        base_url = f"https://res.cloudinary.com/{cloud_name}/{resource_type}/upload"
        
        if transformation:
            # Convert transformation dict to URL parameters
            trans_params = []
            for key, value in transformation.items():
                trans_params.append(f"{key}_{value}")
            trans_string = "/".join(trans_params)
            return f"{base_url}/{trans_string}/{public_id}"
        else:
            return f"{base_url}/{public_id}"
            
    except Exception as e:
        logger.error(f"Error generating Cloudinary URL: {e}")
        return None

def get_image_url(image_field, transformation='medium'):
    """
    Get a Cloudinary URL for an image with a specific transformation.
    
    Args:
        image_field: Django ImageField instance
        transformation (str): Transformation name ('thumbnail', 'medium', 'large', 'profile')
    
    Returns:
        str: The Cloudinary URL or None if not available
    """
    if not image_field:
        return None
        
    try:
        # Get the public ID from the field
        if hasattr(image_field, 'url'):
            # Extract public ID from the URL
            url = image_field.url
            if 'cloudinary.com' in url:
                # Extract public ID from Cloudinary URL
                parts = url.split('/')
                if len(parts) > 2:
                    public_id = parts[-1].split('.')[0]  # Remove file extension
                    
                    # Get transformation settings
                    transformations = settings.CLOUDINARY_STORAGE.get('STATIC_TRANSFORMATIONS', {})
                    if transformation in transformations:
                        return get_cloudinary_url(public_id, transformations[transformation])
                    else:
                        return get_cloudinary_url(public_id)
        
        # Fallback to original URL
        return image_field.url if hasattr(image_field, 'url') else None
        
    except Exception as e:
        logger.error(f"Error getting image URL: {e}")
        return None

def get_video_url(video_field, transformation='medium'):
    """
    Get a Cloudinary URL for a video with a specific transformation.
    
    Args:
        video_field: Django FileField instance
        transformation (str): Transformation name ('thumbnail', 'medium', 'preview')
    
    Returns:
        str: The Cloudinary URL or None if not available
    """
    if not video_field:
        return None
        
    try:
        # Get the public ID from the field
        if hasattr(video_field, 'url'):
            # Extract public ID from the URL
            url = video_field.url
            if 'cloudinary.com' in url:
                # Extract public ID from Cloudinary URL
                parts = url.split('/')
                if len(parts) > 2:
                    public_id = parts[-1].split('.')[0]  # Remove file extension
                    
                    # Get transformation settings
                    transformations = settings.CLOUDINARY_STORAGE.get('VIDEO_TRANSFORMATIONS', {})
                    if transformation in transformations:
                        return get_cloudinary_url(public_id, transformations[transformation], 'video')
                    else:
                        return get_cloudinary_url(public_id, resource_type='video')
        
        # Fallback to original URL
        return video_field.url if hasattr(video_field, 'url') else None
        
    except Exception as e:
        logger.error(f"Error getting video URL: {e}")
        return None

def upload_to_cloudinary(file_obj, folder=None, public_id=None, resource_type='auto'):
    """
    Upload a file directly to Cloudinary.
    
    Args:
        file_obj: File object to upload
        folder (str): Optional folder path
        public_id (str): Optional public ID
        resource_type (str): Resource type ('image', 'video', 'auto')
    
    Returns:
        dict: Cloudinary upload response or None if failed
    """
    try:
        if not hasattr(settings, 'CLOUDINARY_STORAGE'):
            logger.warning("Cloudinary not configured")
            return None
            
        cloud_name = settings.CLOUDINARY_STORAGE.get('CLOUD_NAME')
        api_key = settings.CLOUDINARY_STORAGE.get('API_KEY')
        api_secret = settings.CLOUDINARY_STORAGE.get('API_SECRET')
        
        if not all([cloud_name, api_key, api_secret]):
            logger.warning("Cloudinary credentials not configured")
            return None
        
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        
        # Prepare upload parameters
        upload_params = {
            'resource_type': resource_type,
            'folder': folder or settings.CLOUDINARY_STORAGE.get('FOLDER', 'talentsearch'),
        }
        
        if public_id:
            upload_params['public_id'] = public_id
            
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(file_obj, **upload_params)
        logger.info(f"File uploaded to Cloudinary: {result.get('public_id')}")
        return result
        
    except Exception as e:
        logger.error(f"Error uploading to Cloudinary: {e}")
        return None

def delete_from_cloudinary(public_id, resource_type='image'):
    """
    Delete a file from Cloudinary.
    
    Args:
        public_id (str): The public ID of the resource to delete
        resource_type (str): Type of resource ('image' or 'video')
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not hasattr(settings, 'CLOUDINARY_STORAGE'):
            logger.warning("Cloudinary not configured")
            return False
            
        cloud_name = settings.CLOUDINARY_STORAGE.get('CLOUD_NAME')
        api_key = settings.CLOUDINARY_STORAGE.get('API_KEY')
        api_secret = settings.CLOUDINARY_STORAGE.get('API_SECRET')
        
        if not all([cloud_name, api_key, api_secret]):
            logger.warning("Cloudinary credentials not configured")
            return False
        
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        
        # Delete from Cloudinary
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        if result.get('result') == 'ok':
            logger.info(f"File deleted from Cloudinary: {public_id}")
            return True
        else:
            logger.error(f"Failed to delete file from Cloudinary: {result}")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting from Cloudinary: {e}")
        return False

def is_cloudinary_configured():
    """
    Check if Cloudinary is properly configured.
    
    Returns:
        bool: True if Cloudinary is configured, False otherwise
    """
    if not hasattr(settings, 'CLOUDINARY_STORAGE'):
        return False
        
    cloud_name = settings.CLOUDINARY_STORAGE.get('CLOUD_NAME')
    api_key = settings.CLOUDINARY_STORAGE.get('API_KEY')
    api_secret = settings.CLOUDINARY_STORAGE.get('API_SECRET')
    
    return all([cloud_name, api_key, api_secret]) and cloud_name != 'dummy_cloud_name' 