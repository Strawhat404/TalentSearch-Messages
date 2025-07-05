# 🚀 Quick Start Guide - Feed Comments API Testing

## ✅ Test Data Ready!

Your test data has been created successfully:

### 🔑 Authentication Credentials
```
Username: testuser
Password: testpass123
```

### 📝 Test Data IDs
```
Post ID: bad93faf-0f7c-4070-a292-d0e6d8232f3e
Comment ID: d27420f9-8d97-41e9-b68f-6addb8bbe444
```

## 🚀 Step-by-Step Testing

### 1. Start the Server
```bash
python manage.py runserver 8000
```

### 2. Import Postman Collection
- Open Postman
- Click "Import"
- Select `feed_comments/Postman_Collection.json`

### 3. Set Collection Variables
Right-click collection → Edit → Variables tab:
```
base_url: http://localhost:8000
auth_token: (leave empty)
post_id: bad93faf-0f7c-4070-a292-d0e6d8232f3e
comment_id: d27420f9-8d97-41e9-b68f-6addb8bbe444
```

### 4. Get Authentication Token
1. **Select "Get Auth Token"**
2. **Update request body:**
   ```json
   {
       "username": "testuser",
       "password": "testpass123"
   }
   ```
3. **Send request**
4. **Copy the `access` token from response**
5. **Update `auth_token` variable with the token**

### 5. Test the Endpoints

#### 🔥 Cool Reply Endpoints to Test:

1. **Create Reply**
   - Method: `POST /api/feed_comments/comments/{comment_id}/reply/`
   - Body: `{"content": "This is my awesome reply!"}`

2. **Get Replies**
   - Method: `GET /api/feed_comments/comments/{comment_id}/replies/`

3. **Get Comment Thread**
   - Method: `GET /api/feed_comments/comments/{comment_id}/thread/`

4. **Get Statistics**
   - Method: `GET /api/feed_comments/comments/{comment_id}/stats/`

5. **Get Top Replies**
   - Method: `GET /api/feed_comments/comments/{comment_id}/top-replies/`

## 📊 Expected Results

### Create Reply Response (201)
```json
{
    "id": "uuid-here",
    "content": "This is my awesome reply!",
    "username": "testuser",
    "profile": {...},
    "created_at": "2024-01-15T10:30:00Z",
    "likes_count": 0,
    "dislikes_count": 0,
    "user_has_liked": false,
    "user_has_disliked": false,
    "engagement_score": 0,
    "is_reply": true
}
```

### Get Statistics Response (200)
```json
{
    "total_replies": 6,
    "total_likes": 0,
    "total_dislikes": 0,
    "reply_users": ["testuser"],
    "engagement_score": 0
}
```

## 🎯 Testing Checklist

- [ ] Authentication works
- [ ] Create reply works
- [ ] Get replies works
- [ ] Get thread works
- [ ] Get statistics works
- [ ] Get top replies works
- [ ] Validation errors work (try empty content)
- [ ] Pagination works

## 🚨 Common Issues

### 401 Unauthorized
- Check that auth_token is set correctly
- Make sure token is valid and not expired

### 404 Not Found
- Verify post_id and comment_id are correct
- Check that the server is running

### 400 Bad Request
- Check request body format
- Ensure content is 1-1000 characters

## 🎉 Success Indicators

✅ **All endpoints return expected status codes**
✅ **Response data includes all required fields**
✅ **Engagement metrics calculate correctly**
✅ **Validation prevents invalid data**

## 📚 Additional Resources

- **Full Documentation**: `feed_comments/API_DOCUMENTATION.md`
- **Testing Guide**: `feed_comments/POSTMAN_TESTING_GUIDE.md`
- **System Summary**: `feed_comments/REPLY_SYSTEM_SUMMARY.md`

Happy Testing! 🚀 