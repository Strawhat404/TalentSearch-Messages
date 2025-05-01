from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from .serializers import UserSerializer, LoginSerializer, AdminLoginSerializer, NotificationSerializer
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_str, force_bytes
from .utils import password_reset_token_generator
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from talentsearch.throttles import AuthRateThrottle

User = get_user_model()

class RegisterView(APIView):
    throttle_classes = [AuthRateThrottle]
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'token': token.key
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    throttle_classes = [AuthRateThrottle]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(request, email=serializer.validated_data['email'], password=serializer.validated_data['password'])
            if user:
                token, created = Token.objects.get_or_create(user=user)
                login(request, user)
                return Response({
                    'id': user.id,
                    'email': user.email,
                    'name': user.name,
                    'token': token.key
                }, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminLoginView(APIView):
    throttle_classes = [AuthRateThrottle]
    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(request, email=serializer.validated_data['email'], password=serializer.validated_data['password'])
            if user and user.is_staff:
                token, created = Token.objects.get_or_create(user=user)
                login(request, user)
                return Response({
                    'id': user.id,
                    'email': user.email,
                    'name': user.name,
                    'role': 'admin',
                    'token': token.key
                }, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(APIView):
    throttle_classes = [AuthRateThrottle]
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)
        token = password_reset_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"http://127.0.0.1:8000{reverse('reset-password')}?uid={uid}&token={token}"
        send_mail(
            'Password Reset Request',
            f'Click the link to reset your password: {reset_link}',
            'noreply@example.com',
            [user.email],
            fail_silently=False,
        )
        return Response({'message': 'Password reset link sent to your email'}, status=status.HTTP_200_OK)

class ResetPasswordView(APIView):
    throttle_classes = [AuthRateThrottle]
    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        if not uid or not token or not new_password:
            return Response({'error': 'UID, token, and new password are required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            uid = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is None or not password_reset_token_generator.check_token(user, token):
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')