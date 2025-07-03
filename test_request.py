#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talentsearch.settings.dev')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.tokens import AccessToken
from authapp.views import TokenAuthenticationMiddleware
from messaging.views import MessageView
from messaging.serializers import MessageSerializer
import json

User = get_user_model()

def test_request():
    print("Testing request authentication...")
    print("=" * 50)
    
    # Get user
    user = User.objects.get(id=9)
    print(f"User: {user.email} (ID: {user.id})")
    
    # Create token
    token = AccessToken.for_user(user)
    print(f"Generated token: {token}")
    
    # Create request
    factory = APIRequestFactory()
    request = factory.post(
        '/api/messages/messages/',
        data=json.dumps({
            'receiver_id': 10,
            'message': 'Hello User 10! This is a test message from User 9.'
        }),
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}'
    )
    
    print(f"Request created with Authorization header")
    print(f"Request user before middleware: {request.user}")
    print(f"Request user is authenticated: {request.user.is_authenticated}")
    
    # Apply middleware
    middleware = TokenAuthenticationMiddleware(lambda r: r)
    request = middleware(request)
    
    print(f"Request user after middleware: {request.user}")
    print(f"Request user is authenticated: {request.user.is_authenticated}")
    
    # Test serializer
    serializer = MessageSerializer(data=request.data, context={'request': request})
    print(f"Serializer is valid: {serializer.is_valid()}")
    if not serializer.is_valid():
        print(f"Serializer errors: {serializer.errors}")
    
    # Test view
    view = MessageView()
    view.request = request
    print(f"View request user: {view.request.user}")
    print(f"View request user is authenticated: {view.request.user.is_authenticated}")

if __name__ == '__main__':
    test_request() 