# Rental Ratings API Documentation

## Overview
The Rental Ratings API provides comprehensive backend-side filtering, search, and analytics for rental item ratings and reviews. This API is designed to work efficiently with mobile applications by handling all filtering and sorting on the backend.

## Base URL
```
/api/rental-ratings/
```

## Authentication
All endpoints require authentication. Include the Authorization header:
```
Authorization: Bearer <your_token>
```

## Endpoints

### 1. List Ratings
**GET** `/api/rental-ratings/ratings/`

Get all ratings with advanced filtering and sorting options.

#### Query Parameters
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `item_id` | UUID | Filter by rental item ID | `?item_id=123e4567-e89b-12d3-a456-426614174000` |
| `user` | UUID | Filter by user ID | `?user=123e4567-e89b-12d3-a456-426614174000` |
| `rating` | Integer | Filter by exact rating (1-5) | `?rating=5` |
| `rating__gte` | Integer | Filter by minimum rating | `?rating__gte=4` |
| `rating__lte` | Integer | Filter by maximum rating | `?rating__lte=3` |
| `rating__in` | List | Filter by multiple ratings | `?rating__in=4,5` |
| `is_verified_purchase` | Boolean | Filter by verified purchases | `?is_verified_purchase=true` |
| `reported` | Boolean | Filter by reported ratings | `?reported=false` |
| `is_edited` | Boolean | Filter by edited ratings | `?is_edited=true` |
| `created_at__gte` | Date | Filter by creation date from | `?created_at__gte=2024-01-01` |
| `created_at__lte` | Date | Filter by creation date to | `?created_at__lte=2024-12-31` |
| `min_rating` | Integer | Custom minimum rating filter | `?min_rating=4` |
| `max_rating` | Integer | Custom maximum rating filter | `?max_rating=5` |
| `date_from` | Date | Filter from date | `?date_from=2024-01-01` |
| `date_to` | Date | Filter to date | `?date_to=2024-12-31` |
| `has_comment` | Boolean | Filter ratings with comments | `?has_comment=true` |
| `verified_only` | Boolean | Show only verified purchases | `?verified_only=true` |
| `recent_only` | Boolean | Show only recent ratings (30 days) | `?recent_only=true` |
| `sort_by` | String | Sort order | `?sort_by=helpful` |
| `search` | String | Search in comments and user info | `?search=great` |
| `ordering` | String | Order by field | `?ordering=-created_at` |

#### Sort Options
- `helpful` - Most helpful first (by helpful votes)
- `rating_high` - Highest rating first
- `rating_low` - Lowest rating first
- `recent` - Most recent first
- `oldest` - Oldest first
- `verified_first` - Verified purchases first

#### Response Example
```json
{
  "count": 150,
  "next": "http://api.example.com/ratings/?page=2",
  "previous": null,
  "results": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "item_id": "456e7890-e89b-12d3-a456-426614174000",
      "user_id": "789e0123-e89b-12d3-a456-426614174000",
      "rating": 5,
      "comment": "Excellent rental experience!",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "is_verified_purchase": true,
      "helpful_votes": 12,
      "reported": false,
      "is_edited": false,
      "user_profile": {
        "name": "John Doe",
        "photo": "https://example.com/photo.jpg"
      },
      "item_details": {
        "id": "456e7890-e89b-12d3-a456-426614174000",
        "name": "Professional Camera",
        "image": "https://example.com/camera.jpg",
        "type": "electronics",
        "category": "photography",
        "daily_rate": "50.00"
      },
      "rating_stats": {
        "average_rating": 4.5,
        "total_ratings": 25,
        "rating_distribution": {
          "1": 0,
          "2": 4,
          "3": 8,
          "4": 10,
          "5": 3
        }
      }
    }
  ]
}
```

### 2. Advanced Search
**GET** `/api/rental-ratings/ratings/search_advanced/`

Advanced search with multiple criteria and relevance scoring.

#### Query Parameters
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `q` | String | Search query | `?q=excellent service` |
| `item_id` | UUID | Filter by item ID | `?item_id=123e4567-e89b-12d3-a456-426614174000` |
| `min_rating` | Integer | Minimum rating | `?min_rating=4` |
| `max_rating` | Integer | Maximum rating | `?max_rating=5` |
| `verified_only` | Boolean | Verified purchases only | `?verified_only=true` |
| `date_range` | String | Date range filter | `?date_range=month` |

#### Date Range Options
- `week` - Last 7 days
- `month` - Last 30 days
- `year` - Last 365 days

#### Response
Returns ratings ordered by relevance score (verified purchases + helpful votes + recency).

### 3. Rating Statistics
**GET** `/api/rental-ratings/ratings/statistics/`

Get comprehensive rating statistics.

#### Query Parameters
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `item_id` | UUID | Get stats for specific item | `?item_id=123e4567-e89b-12d3-a456-426614174000` |
| `user_id` | UUID | Get stats for specific user | `?user_id=123e4567-e89b-12d3-a456-426614174000` |

#### Response Example (Item Statistics)
```json
{
  "average_rating": 4.5,
  "total_ratings": 25,
  "rating_distribution": {
    "1": 0,
    "2": 4,
    "3": 8,
    "4": 10,
    "5": 3
  },
  "verified_ratings": 15,
  "recent_ratings": 8
}
```

#### Response Example (Global Statistics)
```json
{
  "total_ratings": 1250,
  "average_rating": 4.2,
  "rating_distribution": {
    "1": 5,
    "2": 8,
    "3": 15,
    "4": 35,
    "5": 37
  },
  "verified_ratings": 800,
  "recent_ratings": 150,
  "top_rated_items": [
    {
      "item_id": "123e4567-e89b-12d3-a456-426614174000",
      "avg_rating": 4.8,
      "count": 25
    }
  ],
  "most_active_users": [
    {
      "user__email": "user@example.com",
      "count": 15
    }
  ]
}
```

### 4. Ratings by Item
**GET** `/api/rental-ratings/ratings/by_item/`

Get all ratings for a specific item with item details and statistics.

#### Query Parameters
| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `item_id` | UUID | Item ID to get ratings for | Yes |

#### Response Example
```json
{
  "item_details": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Professional Camera",
    "image": "https://example.com/camera.jpg"
  },
  "statistics": {
    "average_rating": 4.5,
    "total_ratings": 25,
    "rating_distribution": {
      "1": 0,
      "2": 4,
      "3": 8,
      "4": 10,
      "5": 3
    },
    "verified_ratings": 15,
    "recent_ratings": 8
  },
  "ratings": {
    "count": 25,
    "next": null,
    "previous": null,
    "results": [...]
  }
}
```

### 5. Create Rating
**POST** `/api/rental-ratings/ratings/`

Create a new rating for a rental item.

#### Request Body
```json
{
  "item_id": "123e4567-e89b-12d3-a456-426614174000",
  "rating": 5,
  "comment": "Excellent rental experience!",
  "is_verified_purchase": true
}
```

#### Response
Returns the created rating with all details.

### 6. Update Rating
**PUT/PATCH** `/api/rental-ratings/ratings/{id}/`

Update an existing rating.

#### Request Body
```json
{
  "rating": 4,
  "comment": "Updated comment"
}
```

### 7. Delete Rating
**DELETE** `/api/rental-ratings/ratings/{id}/`

Delete a rating.

#### Response
```json
{
  "message": "Rating deleted successfully."
}
```

### 8. Mark Rating as Helpful
**POST** `/api/rental-ratings/ratings/{id}/mark_helpful/`

Mark a rating as helpful (increments helpful_votes).

#### Response
```json
{
  "message": "Rating marked as helpful",
  "helpful_votes": 13
}
```

### 9. Report Rating
**POST** `/api/rental-ratings/ratings/{id}/report/`

Report a rating for inappropriate content.

#### Response
```json
{
  "message": "Rating reported successfully"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "Validation error",
  "details": {
    "rating": ["Rating must be between 1 and 5"],
    "item_id": ["Rental item does not exist"]
  }
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
  "detail": "Rating not found."
}
```

## Mobile App Integration Examples

### Filtering by Rating Range
```
GET /api/rental-ratings/ratings/?min_rating=4&max_rating=5&sort_by=recent
```

### Search with Multiple Criteria
```
GET /api/rental-ratings/ratings/search_advanced/?q=excellent&verified_only=true&date_range=month
```

### Get Item Statistics
```
GET /api/rental-ratings/ratings/statistics/?item_id=123e4567-e89b-12d3-a456-426614174000
```

### Get All Ratings for Item
```
GET /api/rental-ratings/ratings/by_item/?item_id=123e4567-e89b-12d3-a456-426614174000
```

## Performance Tips

1. **Use pagination** for large result sets
2. **Combine filters** to reduce data transfer
3. **Use specific endpoints** like `/by_item/` for item-specific data
4. **Cache statistics** on the client side
5. **Use search_advanced** for complex queries instead of multiple API calls

## Rate Limiting

- 1000 requests per hour per user
- 100 requests per minute per user
- Burst limit: 10 requests per second per user 