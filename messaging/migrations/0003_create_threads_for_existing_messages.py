# Generated by Django 5.2 on 2025-05-23 21:04

from django.db import migrations

def create_threads_for_messages(apps, schema_editor):
    Message = apps.get_model('messaging', 'Message')
    MessageThread = apps.get_model('messaging', 'MessageThread')
    
    # Group messages by sender and receiver pairs
    message_groups = {}
    for message in Message.objects.all():
        key = tuple(sorted([message.sender_id, message.receiver_id]))
        if key not in message_groups:
            message_groups[key] = []
        message_groups[key].append(message)
    
    # Create threads for each group and associate messages
    for (user1_id, user2_id), messages in message_groups.items():
        # Create a thread for this conversation
        thread = MessageThread.objects.create(
            title=f"Conversation between users {user1_id} and {user2_id}"
        )
        # Add participants
        thread.participants.add(user1_id, user2_id)
        # Associate messages with the thread
        for message in messages:
            message.thread = thread
            message.save()

def reverse_migration(apps, schema_editor):
    Message = apps.get_model('messaging', 'Message')
    MessageThread = apps.get_model('messaging', 'MessageThread')
    
    # Remove thread associations
    Message.objects.all().update(thread=None)
    # Delete all threads
    MessageThread.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ("messaging", "0002_alter_message_options_message_updated_at_and_more"),
    ]

    operations = [
        migrations.RunPython(create_threads_for_messages, reverse_migration),
    ]
