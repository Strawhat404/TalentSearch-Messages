# Messaging API Documentation

## Overview
The messaging system allows users to send and receive messages. Messages are organized into threads (conversations) between participants.

## Authentication
All endpoints require authentication using JWT tokens:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. Get All Messages (Threads)
**GET** `/api/messages/messages/`

Returns all message threads for the authenticated user.

**Response:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "participants": [
        {
          "id": 1,
          "username": "user1"
        },
        {
          "id": 2,
          "username": "user2"
        }
      ],
      "last_message": {
        "id": 5,
        "sender": {
          "id": 1,
          "username": "user1"
        },
        "content": "Hello there!",
        "timestamp": "2024-01-15T10:30:00Z",
        "is_read": false
      },
      "unread_count": 2,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### 2. Get Messages in a Thread
**GET** `/api/messages/messages/{thread_id}/`

Returns all messages in a specific thread.

**Response:**
```json
{
  "id": 1,
  "participants": [
    {
      "id": 1,
      "username": "user1"
    },
    {
      "id": 2,
      "username": "user2"
    }
  ],
  "messages": [
    {
      "id": 1,
      "sender": {
        "id": 1,
        "username": "user1"
      },
      "content": "Hi!",
      "timestamp": "2024-01-15T10:00:00Z",
      "is_read": true
    },
    {
      "id": 2,
      "sender": {
        "id": 2,
        "username": "user2"
      },
      "content": "Hello!",
      "timestamp": "2024-01-15T10:05:00Z",
      "is_read": true
    }
  ],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:05:00Z"
}
```

### 3. Send a Message
**POST** `/api/messages/messages/`

Send a new message to start a conversation or reply to an existing thread.

**Request Body:**
```json
{
  "recipient_id": 2,
  "content": "Hello, how are you?"
}
```

**Response:**
```json
{
  "id": 3,
  "thread": {
    "id": 1,
    "participants": [
      {
        "id": 1,
        "username": "user1"
      },
      {
        "id": 2,
        "username": "user2"
      }
    ]
  },
  "sender": {
    "id": 1,
    "username": "user1"
  },
  "content": "Hello, how are you?",
  "timestamp": "2024-01-15T11:00:00Z",
  "is_read": false
}
```

### 4. Mark Messages as Read
**PATCH** `/api/messages/messages/{thread_id}/mark_read/`

Mark all messages in a thread as read.

**Response:**
```json
{
  "message": "Messages marked as read",
  "thread_id": 1
}
```

## How Messaging Works

### Thread Creation
- When you send a message to someone, the system automatically creates a thread
- If a thread already exists between you and the recipient, the message is added to that thread
- Threads are unique per pair of users

### Message Flow
1. **Send Message**: POST to `/api/messages/messages/` with `recipient_id` and `content`
2. **Get Threads**: GET `/api/messages/messages/` to see all your conversations
3. **View Messages**: GET `/api/messages/messages/{thread_id}/` to see messages in a thread
4. **Mark Read**: PATCH `/api/messages/messages/{thread_id}/mark_read/` when user reads messages

### Frontend Usage

#### Getting User IDs
To send messages, you need the recipient's user ID. You can get this from:
- User search results
- User profiles
- User lists

#### Example Frontend Flow
```javascript
// 1. Get all user's message threads
const threads = await fetch('/api/messages/messages/', {
  headers: { 'Authorization': `Bearer ${token}` }
});

// 2. Send a message to user ID 123
const message = await fetch('/api/messages/messages/', {
  method: 'POST',
  headers: { 
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    recipient_id: 123,
    content: "Hello!"
  })
});

// 3. Get messages in thread ID 1
const threadMessages = await fetch('/api/messages/messages/1/', {
  headers: { 'Authorization': `Bearer ${token}` }
});

// 4. Mark thread as read
await fetch('/api/messages/messages/1/mark_read/', {
  method: 'PATCH',
  headers: { 'Authorization': `Bearer ${token}` }
});
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "Validation error",
  "details": "Recipient ID is required"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Thread not found"
}
```

## Rate Limiting
- 100 requests per minute per user
- 1000 requests per hour per user

## Notes
- `recipient_id` must be a valid user ID (not profile ID)
- Messages are automatically marked as unread for recipients
- Threads are created automatically when sending first message
- All timestamps are in ISO 8601 format (UTC) 