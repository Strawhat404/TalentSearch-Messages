from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import ContactMessage
from .serializers import ContactMessageSerializer
from django.core.mail import send_mail
from django.conf import settings
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ContactView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        if serializer.is_valid():
            contact_message = serializer.save()

            recipient_email = settings.CONTACT_RECIPIENT_EMAIL
            subject = f"New Contact Message: {contact_message.subject}"
            message = f"Name: {contact_message.name}\nEmail: {contact_message.email}\nMessage: {contact_message.message}"
            from_email = settings.DEFAULT_FROM_EMAIL

            logger.debug(f"Email settings - Host: {settings.EMAIL_HOST}, User: {settings.EMAIL_HOST_USER}, From: {from_email}")
            logger.debug(f"Attempting to send email to {recipient_email}")

            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=[recipient_email],
                    fail_silently=False,
                )
                logger.debug("Email sent successfully")
                return Response({"message": "Message sent successfully."}, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Email sending failed: {str(e)}")
                return Response({"message": f"Message saved, but email failed to send: {str(e)}"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)