#!/usr/bin/env python
"""
Test script to verify Cloudinary configuration and functionality.
Run this script to test if Cloudinary is properly configured and working.
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talentsearch.settings.dev')
django.setup()

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import tempfile

def test_cloudinary_configuration():
    """Test if Cloudinary is properly configured."""
    print("🔍 Testing Cloudinary Configuration...")
    
    # Check if Cloudinary settings are present
    if hasattr(settings, 'CLOUDINARY_STORAGE'):
        print(f"✅ CLOUDINARY_STORAGE found in settings")
        print(f"   Cloud Name: {settings.CLOUDINARY_STORAGE.get('CLOUD_NAME', 'Not set')}")
        print(f"   API Key: {settings.CLOUDINARY_STORAGE.get('API_KEY', 'Not set')[:10]}..." if settings.CLOUDINARY_STORAGE.get('API_KEY') else "   API Key: Not set")
        print(f"   API Secret: {'Set' if settings.CLOUDINARY_STORAGE.get('API_SECRET') else 'Not set'}")
    else:
        print("❌ CLOUDINARY_STORAGE not found in settings")
        return False
    
    # Check if all required credentials are set
    cloud_name = settings.CLOUDINARY_STORAGE.get('CLOUD_NAME')
    api_key = settings.CLOUDINARY_STORAGE.get('API_KEY')
    api_secret = settings.CLOUDINARY_STORAGE.get('API_SECRET')
    
    if not all([cloud_name, api_key, api_secret]):
        print("❌ Missing Cloudinary credentials")
        return False
    
    print("✅ All Cloudinary credentials are set")
    return True

def test_storage_backend():
    """Test which storage backend is being used."""
    print("\n🔍 Testing Storage Backend...")
    
    # Debug information
    print(f"DEFAULT_FILE_STORAGE setting: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set')}")
    print(f"MEDIA_ROOT setting: {getattr(settings, 'MEDIA_ROOT', 'Not set')}")
    print(f"MEDIA_URL setting: {getattr(settings, 'MEDIA_URL', 'Not set')}")
    
    storage_class = type(default_storage).__name__
    storage_module = type(default_storage).__module__
    print(f"Current storage backend: {storage_class}")
    print(f"Storage module: {storage_module}")
    
    # Check if it's Cloudinary storage
    if ('cloudinary' in storage_module.lower() or 
        'cloudinary' in str(default_storage).lower() or
        'MediaCloudinaryStorage' in str(default_storage) or
        'cloudinary_storage' in storage_module.lower()):
        print("✅ Using Cloudinary storage backend")
        return True
    elif 'filesystem' in storage_module.lower():
        print("⚠️  Using local filesystem storage backend")
        return False
    else:
        print(f"⚠️  Using unknown storage backend: {storage_class}")
        # Check if the storage is actually working with Cloudinary
        try:
            test_content = b"test"
            test_filename = "storage_test.txt"
            cloudinary_path = default_storage.save(test_filename, ContentFile(test_content))
            if 'cloudinary.com' in cloudinary_path or 'res.cloudinary.com' in cloudinary_path:
                print("✅ Storage is working with Cloudinary URLs")
                default_storage.delete(cloudinary_path)
                return True
            else:
                print("⚠️  Storage is not using Cloudinary URLs")
                default_storage.delete(cloudinary_path)
                return False
        except Exception as e:
            print(f"❌ Error testing storage: {e}")
            return False

def test_file_upload():
    """Test uploading a file to Cloudinary."""
    print("\n🔍 Testing File Upload...")
    
    try:
        # Create a temporary test file
        test_content = b"This is a test file for Cloudinary upload"
        test_filename = "test_cloudinary.txt"
        
        # Upload to Cloudinary
        cloudinary_path = default_storage.save(test_filename, ContentFile(test_content))
        print(f"✅ File uploaded successfully: {cloudinary_path}")
        
        # Check if file exists
        if default_storage.exists(cloudinary_path):
            print("✅ File exists in storage")
            
            # Read the file back
            with default_storage.open(cloudinary_path, 'rb') as f:
                content = f.read()
                if content == test_content:
                    print("✅ File content matches original")
                else:
                    print("❌ File content does not match original")
            
            # Clean up - delete the test file
            default_storage.delete(cloudinary_path)
            print("✅ Test file cleaned up")
            
        else:
            print("❌ File does not exist in storage")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error during file upload test: {str(e)}")
        return False

def test_environment_variables():
    """Test if environment variables are properly set."""
    print("\n🔍 Testing Environment Variables...")
    
    required_vars = ['CLOUD_NAME', 'API_KEY', 'API_SECRET']
    missing_vars = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {value[:10]}..." if var != 'CLOUD_NAME' else f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are set")
    return True

def main():
    """Run all tests."""
    print("🚀 Starting Cloudinary Configuration Tests\n")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Cloudinary Configuration", test_cloudinary_configuration),
        ("Storage Backend", test_storage_backend),
        ("File Upload", test_file_upload),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error in {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Cloudinary is properly configured.")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 