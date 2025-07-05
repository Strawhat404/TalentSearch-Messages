from django.db import migrations

def remove_orphaned_userfollows(apps, schema_editor):
    UserFollow = apps.get_model('feed_posts', 'UserFollow')
    Profile = apps.get_model('userprofile', 'Profile')
    # Remove follows where follower or following profile does not exist
    UserFollow.objects.exclude(follower_id__in=Profile.objects.values_list('id', flat=True)).delete()
    UserFollow.objects.exclude(following_id__in=Profile.objects.values_list('id', flat=True)).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('feed_posts', '0006_add_profile_field_only'),  # or your latest migration
    ]

    operations = [
        migrations.RunPython(remove_orphaned_userfollows),
    ]
