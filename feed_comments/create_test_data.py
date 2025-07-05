#!/usr/bin/env python
"""
Test Data Creation Script for Feed Comments API
This script creates test users, posts, and comments for Postman testing.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talentsearch.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from feed_posts.models import FeedPost
from feed_comments.models import Comment
from userprofile.models import BasicInformation

User = get_user_model()

def create_test_data():
    """Create test data for API testing"""
    
    print("🚀 Creating test data for Feed Comments API...")
    
    # Create test user
    try:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        print(f"✅ Created user: {user.username}")
    except:
        user = User.objects.get(username='testuser')
        print(f"✅ Using existing user: {user.username}")
    
    # Create user profile
    try:
        profile = BasicInformation.objects.create(
            user=user,
            first_name='Test',
            last_name='User',
            date_of_birth='1990-01-01'
        )
        print(f"✅ Created profile for: {user.username}")
    except:
        print(f"✅ Profile already exists for: {user.username}")
    
    # Create test post
    try:
        post = FeedPost.objects.create(
            user=user,
            content='This is a test post for API testing. Feel free to comment on this post!'
        )
        print(f"✅ Created post: {post.id}")
    except Exception as e:
        print(f"⚠️  Error creating post: {e}")
        return
    
    # Create test comments
    comments = []
    comment_texts = [
        "This is a great post! Thanks for sharing.",
        "I really enjoyed reading this. Very informative!",
        "Interesting perspective on this topic.",
        "Looking forward to more posts like this.",
        "This resonates with me a lot."
    ]
    
    for i, text in enumerate(comment_texts):
        try:
            comment = Comment.objects.create(
                post=post,
                user=user,
                content=text
            )
            comments.append(comment)
            print(f"✅ Created comment {i+1}: {comment.id}")
        except Exception as e:
            print(f"⚠️  Error creating comment {i+1}: {e}")
    
    # Create test replies
    if comments:
        reply_texts = [
            "I agree with this comment!",
            "Great point, thanks for sharing.",
            "This is exactly what I was thinking.",
            "Well said!",
            "I have a different perspective on this."
        ]
        
        for i, reply_text in enumerate(reply_texts):
            try:
                reply = Comment.objects.create(
                    post=post,
                    user=user,
                    content=reply_text,
                    parent=comments[i % len(comments)]  # Distribute replies across comments
                )
                print(f"✅ Created reply {i+1}: {reply.id}")
            except Exception as e:
                print(f"⚠️  Error creating reply {i+1}: {e}")
    
    print("\n🎉 Test data creation completed!")
    print(f"\n📋 Test Data Summary:")
    print(f"   User: {user.username} (ID: {user.id})")
    print(f"   Post: {post.id}")
    print(f"   Comments: {len(comments)}")
    print(f"   Replies: {len(reply_texts) if comments else 0}")
    
    print(f"\n🔑 Authentication:")
    print(f"   Username: {user.username}")
    print(f"   Password: testpass123")
    
    print(f"\n📝 Postman Variables to Set:")
    print(f"   post_id: {post.id}")
    print(f"   comment_id: {comments[0].id if comments else 'N/A'}")
    
    print(f"\n🚀 Ready for Postman testing!")
    print(f"   1. Start the server: python manage.py runserver 8000")
    print(f"   2. Import the Postman collection")
    print(f"   3. Get auth token using the credentials above")
    print(f"   4. Set the variables and start testing!")

if __name__ == '__main__':
    create_test_data() 