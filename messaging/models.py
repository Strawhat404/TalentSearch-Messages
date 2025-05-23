from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils.html import strip_tags
import bleach

class MessageThread(models.Model):
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='threads',
        help_text="Users participating in this conversation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Optional title for the conversation"
    )

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        if self.title:
            return self.title
        participants = self.participants.all()[:2]
        names = [p.name for p in participants]
        if len(self.participants.all()) > 2:
            names.append(f"+{len(self.participants.all()) - 2} more")
        return " - ".join(names)

    def get_last_message(self):
        """Get the most recent message in the thread"""
        return self.messages.order_by('-created_at').first()

    def mark_as_read(self, user):
        """Mark all messages in thread as read for a specific user"""
        self.messages.filter(receiver=user, is_read=False).update(is_read=True)

class Message(models.Model):
    thread = models.ForeignKey(
        MessageThread,
        related_name='messages',
        on_delete=models.CASCADE,
        help_text="The conversation this message belongs to",
        null=True,  # Make it nullable initially
        blank=True  # Allow blank in forms
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='sent_messages',
        on_delete=models.CASCADE,
        help_text="User who sent the message"
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='received_messages',
        on_delete=models.CASCADE,
        help_text="User who should receive the message"
    )
    message = models.TextField(
        validators=[
            MinLengthValidator(1, message="Message cannot be empty"),
            MaxLengthValidator(5000, message="Message cannot exceed 5000 characters")
        ],
        help_text="The message content"
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver} at {self.created_at}"

    def clean(self):
        """Validate the message"""
        # Ensure sender and receiver are participants in the thread
        if self.thread and self.sender and self.receiver:
            if self.sender not in self.thread.participants.all():
                raise ValidationError("Sender must be a participant in the thread")
            if self.receiver not in self.thread.participants.all():
                raise ValidationError("Receiver must be a participant in the thread")

        # Sanitize message content
        if self.message:
            # First strip HTML tags
            clean_message = strip_tags(self.message)
            # Then sanitize using bleach
            self.message = bleach.clean(
                clean_message,
                strip=True,
                strip_comments=True,
                tags=[],  # No HTML tags allowed
                attributes={},
                protocols=[]
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        # Update thread's updated_at timestamp if thread exists
        if self.thread:
            self.thread.save()  # This will update the updated_at field
