# Notification System API Documentation

## Overview

The notification system provides a comprehensive set of endpoints for managing user notifications. The system supports various notification types, real-time updates, and security features.

## Base URL
```
/api/auth/
```

## Authentication
All notification endpoints require authentication using JWT tokens. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Notification Types
The system supports the following notification types:
- `info` - General information
- `warning` - Warning messages
- `alert` - Important alerts
- `system` - System notifications
- `security` - Security-related notifications
- `account` - Account-related notifications
- `message` - New messages
- `job` - Job-related notifications
- `news` - News updates
- `comment` - New comments
- `like` - New likes
- `rating` - Rating notifications
- `rental` - Rental-related notifications
- `advert` - Advertisement notifications
- `profile` - Profile updates
- `verification` - Verification notifications
- `payment` - Payment notifications
- `support` - Support notifications

## API Endpoints

### 1. List Notifications
**GET** `/notifications/`

Get all notifications for the authenticated user.

**Response:**
```json
[
  {
    "id": 1,
    "title": "Welcome!",
    "message": "Welcome to our platform",
    "notification_type": "info",
    "read": false,
    "link": "https://example.com/welcome",
    "data": {
      "action": "view_profile"
    },
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### 2. Create Notification
**POST** `/notifications/`

Create a new notification for the authenticated user.

**Request Body:**
```json
{
  "title": "New Message",
  "message": "You have received a new message",
  "notification_type": "message",
  "link": "https://example.com/messages",
  "data": {
    "sender_id": 123,
    "message_id": 456
  }
}
```

### 3. Get Notification Details
**GET** `/notifications/{id}/`

Get details of a specific notification.

**Response:**
```json
{
  "id": 1,
  "title": "Welcome!",
  "message": "Welcome to our platform",
  "notification_type": "info",
  "read": false,
  "link": "https://example.com/welcome",
  "data": {
    "action": "view_profile"
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 4. Mark Notification as Read
**POST** `/notifications/mark-read/`

Mark a specific notification as read.

**Request Body:**
```json
{
  "notification_id": 1
}
```

**Response:**
```json
{
  "message": "Notification marked as read",
  "success": true
}
```

### 5. Mark All Notifications as Read
**POST** `/notifications/mark-all-read/`

Mark all notifications as read for the authenticated user.

**Response:**
```json
{
  "message": "All notifications marked as read",
  "count": 5
}
```

### 6. Get Unread Count
**GET** `/notifications/unread-count/`

Get the number of unread notifications.

**Response:**
```json
{
  "unread_count": 3
}
```

### 7. Delete Notification
**DELETE** `/notifications/{id}/`

Delete a specific notification using the RESTful DELETE method.

**Response:**
```json
204 No Content
```

**Note:** This is the only way to delete notifications. Use the DELETE HTTP method with the notification ID in the URL.

### 8. Get Notification Statistics
**GET** `/notifications/stats/`

Get notification statistics for the authenticated user.

**Response:**
```json
{
  "total_count": 25,
  "unread_count": 3,
  "read_count": 22,
  "by_type": {
    "info": 10,
    "warning": 5,
    "alert": 2,
    "system": 8
  }
}
```

### 9. Create System Notification (Admin Only)
**POST** `/notifications/system/`

Create a system notification for all users or specific users (admin only).

**Request Body:**
```json
{
  "title": "System Maintenance",
  "message": "System will be down for maintenance",
  "link": "https://example.com/maintenance",
  "user_ids": [1, 2, 3]
}
```

**Response:**
```json
{
  "message": "System notification created",
  "count": 150
}
```

### 10. Cleanup Old Notifications (Admin Only)
**POST** `/notifications/cleanup/`

Clean up notifications older than specified days (admin only).

**Request Body:**
```json
{
  "days": 30
}
```

**Response:**
```json
{
  "message": "Old notifications cleaned up",
  "deleted_count": 150
}
```

## Frontend Integration Examples

### JavaScript/React Example

```javascript
// Get notifications
const getNotifications = async () => {
  const response = await fetch('/api/auth/notifications/', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};

// Mark notification as read
const markAsRead = async (notificationId) => {
  const response = await fetch('/api/auth/notifications/mark-read/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ notification_id: notificationId })
  });
  return response.json();
};

// Get unread count
const getUnreadCount = async () => {
  const response = await fetch('/api/auth/notifications/unread-count/', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return response.json();
};
```

### Real-time Updates

To implement real-time notifications, you can:

1. **Poll for updates**: Periodically call the unread count endpoint
2. **WebSocket integration**: Use Django Channels for real-time updates
3. **Server-Sent Events**: Implement SSE for real-time notifications

### Notification Badge Example

```javascript
// Update notification badge
const updateNotificationBadge = async () => {
  try {
    const { unread_count } = await getUnreadCount();
    const badge = document.getElementById('notification-badge');
    badge.textContent = unread_count;
    badge.style.display = unread_count > 0 ? 'block' : 'none';
  } catch (error) {
    console.error('Error updating notification badge:', error);
  }
};

// Call this function periodically or after user actions
setInterval(updateNotificationBadge, 30000); // Update every 30 seconds
```

## Error Handling

### Common Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden:**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**404 Not Found:**
```json
{
  "error": "Notification not found or could not be marked as read"
}
```

**400 Bad Request:**
```json
{
  "error": "notification_id is required"
}
```

## Security Features

1. **User Isolation**: Users can only access their own notifications
2. **XSS Prevention**: All notification content is sanitized
3. **Admin Controls**: System notifications require admin privileges
4. **Rate Limiting**: Endpoints are protected against abuse
5. **Input Validation**: All inputs are validated and sanitized

## Best Practices

1. **Cache Unread Count**: Cache the unread count to reduce API calls
2. **Batch Operations**: Use mark-all-read for better UX
3. **Error Handling**: Always handle API errors gracefully
4. **Loading States**: Show loading states during API calls
5. **Optimistic Updates**: Update UI immediately, then sync with server

## Testing

The notification system includes comprehensive tests covering:
- Service layer functionality
- API endpoint behavior
- Security features
- Integration with other systems
- Error handling

Run tests with:
```bash
python manage.py test authapp.tests_notifications
```

## Migration Notes

If you're upgrading from an older version:

1. Run migrations: `python manage.py migrate`
2. The new system is backward compatible
3. Old notifications will be preserved
4. New fields (data, link) are optional

## Support

For issues or questions about the notification system:
1. Check the test files for usage examples
2. Review the service layer code for implementation details
3. Contact the backend team for technical support 