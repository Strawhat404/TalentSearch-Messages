# 🚀 Feed Comments API - Postman Testing Guide

## 📋 Prerequisites

1. **Start the Django Server**
   ```bash
   python manage.py runserver 8000
   ```

2. **Import the Postman Collection**
   - Open Postman
   - Click "Import" 
   - Select the `Postman_Collection.json` file from the `feed_comments` folder

## 🔧 Setup Variables

Before testing, you need to set up the collection variables:

1. **Open Collection Variables**
   - Right-click on the collection name
   - Select "Edit"
   - Go to the "Variables" tab

2. **Set the following variables:**
   ```
   base_url: http://localhost:8000
   auth_token: (leave empty for now)
   post_id: (leave empty for now)
   comment_id: (leave empty for now)
   ```

## 🔐 Step 1: Authentication

### Get Auth Token
1. **Open the "Authentication" folder**
2. **Select "Get Auth Token"**
3. **Update the request body:**
   ```json
   {
       "username": "your_actual_username",
       "password": "your_actual_password"
   }
   ```
4. **Send the request**
5. **Copy the `access` token from the response**
6. **Update the `auth_token` variable with your token**

## 📝 Step 2: Create Test Data

### Create a Post (if needed)
You'll need a post ID to test comments. If you don't have one, create a post first using the feed_posts API.

### Create a Comment
1. **Open the "Comments" folder**
2. **Select "Create Comment"**
3. **Update the request body:**
   ```json
   {
       "post": "your_post_id_here",
       "content": "This is a test comment for Postman testing!"
   }
   ```
4. **Send the request**
5. **Copy the comment ID from the response**
6. **Update the `comment_id` variable with this ID**

## 🧪 Step 3: Test Basic Comment Endpoints

### Test Get Comments
1. **Select "Get Comments"**
2. **Send the request**
3. **Verify you get a list of comments for the post**

### Test Get Single Comment
1. **Select "Get Single Comment"**
2. **Send the request**
3. **Verify you get the specific comment details**

### Test Like Comment
1. **Select "Like Comment"**
2. **Send the request**
3. **Verify the likes_count increases**

## 🚀 Step 4: Test Cool Reply Endpoints

### Test Create Reply
1. **Open the "🔥 Cool Reply Endpoints" folder**
2. **Select "Create Reply"**
3. **Update the request body:**
   ```json
   {
       "content": "This is my awesome reply to the comment!"
   }
   ```
4. **Send the request**
5. **Verify you get a 201 response with reply data**

### Test Get Replies
1. **Select "Get Replies"**
2. **Send the request**
3. **Verify you get the list of replies**

### Test Get Comment Thread
1. **Select "Get Comment Thread"**
2. **Send the request**
3. **Verify you get the comment with all its replies**

### Test Get Comment Statistics
1. **Select "Get Comment Statistics"**
2. **Send the request**
3. **Verify you get engagement metrics:**
   ```json
   {
       "total_replies": 1,
       "total_likes": 1,
       "total_dislikes": 0,
       "reply_users": ["username"],
       "engagement_score": 3
   }
   ```

### Test Get Top Replies
1. **Select "Get Top Replies"**
2. **Send the request**
3. **Verify you get replies sorted by engagement**

## 🔄 Step 5: Test Advanced Scenarios

### Test Multiple Replies
1. **Create multiple replies to the same comment**
2. **Test the pagination in "Get Replies"**
3. **Verify the statistics update correctly**

### Test Like/Dislike Replies
1. **Like some replies**
2. **Check the engagement scores change**
3. **Verify "Get Top Replies" sorts correctly**

### Test Validation
1. **Try to create a reply with empty content**
2. **Try to create a reply with very long content (>1000 chars)**
3. **Verify you get proper validation errors**

## 📊 Expected Responses

### Create Reply Response
```json
{
    "id": "uuid-here",
    "content": "This is my awesome reply!",
    "user": "user-id",
    "username": "john_doe",
    "profile": {
        "profile_photo": "url-here",
        "bio": "User bio"
    },
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "likes_count": 0,
    "dislikes_count": 0,
    "user_has_liked": false,
    "user_has_disliked": false,
    "engagement_score": 0,
    "is_reply": true
}
```

### Get Statistics Response
```json
{
    "total_replies": 2,
    "total_likes": 5,
    "total_dislikes": 1,
    "reply_users": ["user1", "user2"],
    "engagement_score": 9
}
```

### Get Thread Response
```json
{
    "id": "comment-uuid",
    "content": "Original comment",
    "username": "original_user",
    "profile": {...},
    "created_at": "2024-01-15T10:00:00Z",
    "likes_count": 5,
    "dislikes_count": 1,
    "user_has_liked": false,
    "user_has_disliked": false,
    "replies": [
        {
            "id": "reply-uuid-1",
            "content": "First reply",
            "username": "user1",
            "profile": {...},
            "created_at": "2024-01-15T10:30:00Z",
            "likes_count": 3,
            "dislikes_count": 0,
            "user_has_liked": true,
            "user_has_disliked": false,
            "engagement_score": 3,
            "is_reply": true
        }
    ]
}
```

## 🚨 Common Issues & Solutions

### Issue: 401 Unauthorized
**Solution:** Make sure you have a valid auth token and it's set in the collection variables.

### Issue: 404 Not Found
**Solution:** Check that your `post_id` and `comment_id` variables are set correctly.

### Issue: 400 Bad Request
**Solution:** Check the request body format and content validation rules.

### Issue: 403 Forbidden
**Solution:** You can only edit/delete your own comments.

## 🎯 Testing Checklist

- [ ] Authentication works
- [ ] Create comment works
- [ ] Get comments works
- [ ] Like comment works
- [ ] Create reply works
- [ ] Get replies works
- [ ] Get thread works
- [ ] Get statistics works
- [ ] Get top replies works
- [ ] Validation errors work
- [ ] Pagination works
- [ ] Engagement scoring works

## 🎉 Success Indicators

✅ **All endpoints return expected status codes**
✅ **Response data includes all required fields**
✅ **Engagement metrics calculate correctly**
✅ **Pagination works for large datasets**
✅ **Validation prevents invalid data**
✅ **Authentication protects endpoints**

## 📝 Notes

- **Base URL**: Make sure your Django server is running on `http://localhost:8000`
- **Authentication**: All endpoints require a valid JWT token
- **Content Limits**: Reply content must be 1-1000 characters
- **Reply Depth**: You can only reply to top-level comments (not replies to replies)
- **Performance**: Large datasets are paginated for better performance

Happy Testing! 🚀 