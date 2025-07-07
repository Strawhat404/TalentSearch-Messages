# feed/models.py

from django.db import models
from userprofile.models import Profile

class FeedPost(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='feed_posts')
    content = models.TextField()
    media = models.FileField(upload_to='media/feed_posts/', blank=True, null=True)
    media_type = models.CharField(max_length=10, choices=[('image', 'Image'), ('video', 'Video')])
    project_title = models.CharField(max_length=200)
    project_type = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

class FeedLike(models.Model):
    post = models.ForeignKey(FeedPost, on_delete=models.CASCADE, related_name='likes')
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='feed_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'profile')

class Follow(models.Model):
    follower = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

class Comment(models.Model):
    post = models.ForeignKey(FeedPost, on_delete=models.CASCADE, related_name='comments')
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)

class CommentLike(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='comment_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comment', 'profile')
