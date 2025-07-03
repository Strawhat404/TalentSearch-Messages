#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talentsearch.settings.dev')
django.setup()

from rest_framework_simplejwt.tokens import AccessToken
from django.conf import settings
import jwt
from authapp.models import User

def test_token():
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzUyMDc5MDA0LCJpYXQiOjE3NTE0NzQyMDQsImp0aSI6Ijk0Nzk2ZThlYjc0MjRmNmNhMGU3MjFlODgxZmM3NWFlIiwidXNlcl9pZCI6OX0.9EM_nP4Mg_kWFA1WdAOQPrX-VRmq1PbFPZYoZV2ajMc'
    
    print("Testing JWT token...")
    print("=" * 50)
    
    try:
        # Decode without verification first to see the payload
        decoded = jwt.decode(token, options={'verify_signature': False})
        print('Token payload:', decoded)
        
        # Now verify with the secret key
        verified = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        print('Token verified successfully')
        print('User ID:', verified.get('user_id'))
        print('Token type:', verified.get('token_type'))
        print('Expires:', verified.get('exp'))
        
        # Check if user exists
        user_id = verified.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                print(f'User found: {user.email} (ID: {user.id})')
                print(f'User is active: {user.is_active}')
            except User.DoesNotExist:
                print(f'User with ID {user_id} does not exist')
        
    except Exception as e:
        print('Error:', e)
    
    print("\nTesting DRF SimpleJWT...")
    print("=" * 50)
    
    try:
        # Test with DRF SimpleJWT
        token_obj = AccessToken(token)
        print('DRF Token verified successfully')
        print('User ID:', token_obj.get('user_id'))
        print('Token type:', token_obj.get('token_type'))
        print('Expires:', token_obj.get('exp'))
        
    except Exception as e:
        print('DRF Error:', e)

if __name__ == '__main__':
    test_token() 