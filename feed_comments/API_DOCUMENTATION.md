# 🚀 Feed Comments API Documentation

## Overview
The Feed Comments API provides a comprehensive system for managing comments and replies on feed posts. The new reply system offers intuitive and cool endpoints for better user engagement.

## 🔥 Cool New Reply Endpoints

### 1. Create Reply
**POST** `/api/feed_comments/comments/{comment_id}/reply/`

Create a reply to a specific comment. This is the main endpoint for reply functionality.

**Request Body:**
```json
{
    "content": "This is my awesome reply!"
}
```

**Response (201 Created):**
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

**Validation Rules:**
- Content cannot be empty
- Content cannot exceed 1000 characters
- Cannot reply to a reply (only top-level comments can have replies)

### 2. Get Replies
**GET** `/api/feed_comments/comments/{comment_id}/replies/`

Get all replies for a specific comment with pagination.

**Query Parameters:**
- `page` - Page number for pagination
- `page_size` - Number of items per page (default: 10)

**Response (200 OK):**
```json
{
    "count": 5,
    "next": "http://api.com/comments/{id}/replies/?page=2",
    "previous": null,
    "results": [
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

### 3. Get Comment Thread
**GET** `/api/feed_comments/comments/{comment_id}/thread/`

Get a complete comment thread with all replies in a nested format.

**Response (200 OK):**
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

### 4. Get Comment Statistics
**GET** `/api/feed_comments/comments/{comment_id}/stats/`

Get comprehensive statistics and engagement metrics for a comment.

**Response (200 OK):**
```json
{
    "total_replies": 5,
    "total_likes": 12,
    "total_dislikes": 2,
    "reply_users": ["user1", "user2", "user3"],
    "engagement_score": 22
}
```

### 5. Get Top Replies
**GET** `/api/feed_comments/comments/{comment_id}/top-replies/`

Get the most popular replies sorted by engagement score.

**Query Parameters:**
- `limit` - Number of top replies to return (default: 5)

**Response (200 OK):**
```json
[
    {
        "id": "popular-reply-uuid",
        "content": "Most popular reply",
        "username": "popular_user",
        "profile": {...},
        "created_at": "2024-01-15T10:30:00Z",
        "likes_count": 15,
        "dislikes_count": 0,
        "user_has_liked": false,
        "user_has_disliked": false,
        "engagement_score": 15,
        "is_reply": true
    }
]
```

## 📊 Engagement Score Calculation

The engagement score is calculated as:
```
engagement_score = likes_count + (replies_count * 2)
```

This weights replies more heavily than likes to encourage meaningful discussions.

## 🔄 Existing Endpoints (Enhanced)

### Create Comment
**POST** `/api/feed_comments/comments/`

**Request Body:**
```json
{
    "post": "post-uuid",
    "content": "My comment content"
}
```

### Get Comments
**GET** `/api/feed_comments/comments/`

**Query Parameters:**
- `post_id` - Filter by post ID
- `parent_id` - Filter by parent comment ID

### Like/Dislike Comment
**POST** `/api/feed_comments/comments/{comment_id}/like/`

**Request Body:**
```json
{
    "is_like": true  // true for like, false for dislike
}
```

## 🛡️ Security & Permissions

- All endpoints require authentication
- Users can only edit/delete their own comments
- Reply creation is restricted to top-level comments only
- Content validation prevents spam and abuse

## 🧪 Testing

Run the comprehensive test suite:
```bash
python manage.py test feed_comments.tests
```

## 📈 Performance Features

- Optimized database queries with select_related and prefetch_related
- Pagination for large reply lists
- Efficient engagement score calculation
- Indexed database fields for fast lookups

## 🎯 Best Practices

1. **Use the dedicated reply endpoints** instead of the generic comment creation
2. **Implement pagination** for large reply lists
3. **Cache engagement scores** for frequently accessed comments
4. **Validate content** on both frontend and backend
5. **Monitor engagement metrics** to identify popular content

## 🔮 Future Enhancements

- Nested reply support (replies to replies)
- Reply threading and conversation flows
- Advanced filtering and sorting options
- Real-time notifications for replies
- Reply moderation and spam detection 