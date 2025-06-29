from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from django.utils import timezone
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
        names = []
        for p in participants:
            if hasattr(p, 'name') and p.name and p.name != 'Unknown User':
                names.append(p.name)
            else:
                names.append(p.email)
        if len(self.participants.all()) > 2:
            names.append(f"+{len(self.participants.all()) - 2} more")
        return " - ".join(names)

    def get_last_message(self):
        """Get the most recent message in the thread"""
        return self.messages.order_by('-created_at').first()

    @classmethod
    def get_last_message_optimized(cls, thread_id):
        """Get the most recent message in the thread with optimized queries"""
        return cls.objects.filter(id=thread_id).first().messages.select_related(
            'sender', 'receiver'
        ).order_by('-created_at').first()

    def mark_as_read(self, user):
        """Mark all messages in thread as read for a specific user"""
        # Mark messages where user is the receiver as read
        self.messages.filter(receiver=user, is_read=False).update(is_read=True)
        
        # In group conversations, also mark messages sent by the user as "read by sender"
        # This provides better UX for group chats
        self.messages.filter(sender=user, is_read=False).update(is_read=True)

    def mark_all_as_read_for_user(self, user):
        """Mark all messages in thread as read for a specific user (alternative method)"""
        # Mark all messages in the thread as read for this user
        # This is useful for group conversations where we want to mark everything as read
        self.messages.filter(is_read=False).update(is_read=True)

    def validate_participants(self, sender, receiver):
        """Validate that sender and receiver are participants in this thread"""
        if sender not in self.participants.all():
            raise ValidationError("Sender must be a participant in the thread")
        if receiver not in self.participants.all():
            raise ValidationError("Receiver must be a participant in the thread")

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
        # Ensure sender and receiver are participants in the thread (only if thread exists)
        if self.thread and self.sender and self.receiver:
            self.thread.validate_participants(self.sender, self.receiver)

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
            # Use update() to avoid race conditions and unnecessary database writes
            MessageThread.objects.filter(id=self.thread.id).update(updated_at=timezone.now())
