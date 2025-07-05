from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from feed_posts.models import FeedPost
from feed_comments.models import Comment
from userprofile.models import BasicInformation

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test data for Feed Comments API testing'

    def handle(self, *args, **options):
        """Create test data for API testing"""
        
        self.stdout.write("🚀 Creating test data for Feed Comments API...")
        
        # Create test user
        try:
            user = User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123'
            )
            self.stdout.write(f"✅ Created user: {user.username}")
        except:
            user = User.objects.get(username='testuser')
            self.stdout.write(f"✅ Using existing user: {user.username}")
        
        # Create user profile
        try:
            profile = BasicInformation.objects.create(
                user=user,
                first_name='Test',
                last_name='User',
                date_of_birth='1990-01-01'
            )
            self.stdout.write(f"✅ Created profile for: {user.username}")
        except:
            self.stdout.write(f"✅ Profile already exists for: {user.username}")
        
        # Create test post
        try:
            post = FeedPost.objects.create(
                user=user,
                content='This is a test post for API testing. Feel free to comment on this post!'
            )
            self.stdout.write(f"✅ Created post: {post.id}")
        except Exception as e:
            self.stdout.write(f"⚠️  Error creating post: {e}")
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
                self.stdout.write(f"✅ Created comment {i+1}: {comment.id}")
            except Exception as e:
                self.stdout.write(f"⚠️  Error creating comment {i+1}: {e}")
        
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
                    self.stdout.write(f"✅ Created reply {i+1}: {reply.id}")
                except Exception as e:
                    self.stdout.write(f"⚠️  Error creating reply {i+1}: {e}")
        
        self.stdout.write("\n🎉 Test data creation completed!")
        self.stdout.write(f"\n📋 Test Data Summary:")
        self.stdout.write(f"   User: {user.username} (ID: {user.id})")
        self.stdout.write(f"   Post: {post.id}")
        self.stdout.write(f"   Comments: {len(comments)}")
        self.stdout.write(f"   Replies: {len(reply_texts) if comments else 0}")
        
        self.stdout.write(f"\n🔑 Authentication:")
        self.stdout.write(f"   Username: {user.username}")
        self.stdout.write(f"   Password: testpass123")
        
        self.stdout.write(f"\n📝 Postman Variables to Set:")
        self.stdout.write(f"   post_id: {post.id}")
        self.stdout.write(f"   comment_id: {comments[0].id if comments else 'N/A'}")
        
        self.stdout.write(f"\n🚀 Ready for Postman testing!")
        self.stdout.write(f"   1. Start the server: python manage.py runserver 8000")
        self.stdout.write(f"   2. Import the Postman collection")
        self.stdout.write(f"   3. Get auth token using the credentials above")
        self.stdout.write(f"   4. Set the variables and start testing!") 