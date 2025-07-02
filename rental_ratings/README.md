# Enhanced Rental Ratings System

## Overview
The Enhanced Rental Ratings System provides comprehensive backend-side filtering, search, and analytics for rental item ratings and reviews. This system is designed to work efficiently with mobile applications by handling all filtering and sorting on the backend, eliminating the need for frontend filtering.

## Features

### 🚀 Core Features
- **Backend-side filtering and sorting** - All filtering happens on the server
- **Advanced search capabilities** - Multi-criteria search with relevance scoring
- **Comprehensive statistics** - Real-time rating analytics and distributions
- **Verified purchase tracking** - Distinguish between verified and unverified ratings
- **Helpful votes system** - Community-driven rating quality
- **Rating reporting** - Moderation capabilities
- **Performance optimized** - Database indexes and efficient queries

### 📊 Analytics & Statistics
- Average ratings with distribution
- Verified vs unverified ratings
- Recent rating trends
- Top-rated items
- Most active users
- Rating history tracking

### 🔍 Advanced Filtering
- Rating range filtering (min/max)
- Date range filtering
- Verified purchase filtering
- Comment presence filtering
- User-based filtering
- Item-based filtering

### 📱 Mobile-Optimized
- Pagination support
- Efficient data transfer
- Caching-friendly responses
- Rate limiting
- Comprehensive error handling

## Installation & Setup

### 1. Run Migrations
```bash
python manage.py makemigrations rental_ratings
python manage.py migrate
```

### 2. Update Rating Statistics (Optional)
If you have existing ratings, update the statistics:
```bash
python manage.py update_rating_statistics
```

### 3. Configure URLs
Add to your main `urls.py`:
```python
path('api/rental-ratings/', include('rental_ratings.urls')),
```

## API Endpoints

### Base URL
```
/api/rental-ratings/
```

### Main Endpoints
- `GET /ratings/` - List ratings with filtering
- `GET /ratings/search_advanced/` - Advanced search
- `GET /ratings/statistics/` - Rating statistics
- `GET /ratings/by_item/` - Item-specific ratings
- `POST /ratings/` - Create rating
- `PUT/PATCH /ratings/{id}/` - Update rating
- `DELETE /ratings/{id}/` - Delete rating
- `POST /ratings/{id}/mark_helpful/` - Mark as helpful
- `POST /ratings/{id}/report/` - Report rating

## Usage Examples

### Mobile App Integration

#### 1. Get Filtered Ratings
```javascript
// Get high-rated verified purchases
const response = await fetch('/api/rental-ratings/ratings/?min_rating=4&verified_only=true&sort_by=recent');
const ratings = await response.json();
```

#### 2. Advanced Search
```javascript
// Search for excellent reviews in the last month
const response = await fetch('/api/rental-ratings/ratings/search_advanced/?q=excellent&date_range=month&verified_only=true');
const results = await response.json();
```

#### 3. Get Item Statistics
```javascript
// Get comprehensive stats for an item
const response = await fetch('/api/rental-ratings/ratings/statistics/?item_id=item-uuid');
const stats = await response.json();
```

#### 4. Create Rating
```javascript
const ratingData = {
  item_id: 'item-uuid',
  rating: 5,
  comment: 'Excellent rental experience!',
  is_verified_purchase: true
};

const response = await fetch('/api/rental-ratings/ratings/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
  },
  body: JSON.stringify(ratingData)
});
```

## Model Fields

### Rating Model
- `id` - UUID primary key
- `item_id` - UUID of the rental item
- `user` - Foreign key to User
- `rating` - Integer (1-5)
- `comment` - Text field
- `created_at` - DateTime
- `updated_at` - DateTime
- `is_verified_purchase` - Boolean
- `helpful_votes` - Integer
- `reported` - Boolean
- `is_edited` - Boolean

## Database Indexes
The system includes optimized database indexes for:
- `item_id + rating` - Fast rating filtering
- `user + created_at` - User rating history
- `rating + created_at` - Rating-based sorting
- `is_verified_purchase + rating` - Verified rating queries

## Performance Optimizations

### 1. Query Optimization
- `select_related` for user and profile data
- `prefetch_related` for related objects
- Database indexes on frequently queried fields
- Efficient aggregation queries

### 2. Caching Strategy
- Statistics can be cached on the client side
- Use pagination for large result sets
- Combine filters to reduce API calls

### 3. Rate Limiting
- 1000 requests per hour per user
- 100 requests per minute per user
- 10 requests per second burst limit

## Testing

### Run Tests
```bash
python manage.py test rental_ratings.test_enhanced_features
```

### Test Coverage
- Model functionality
- API endpoints
- Filtering and search
- Statistics calculation
- Performance testing
- Error handling

## Management Commands

### Update Rating Statistics
```bash
# Update all items
python manage.py update_rating_statistics

# Update specific item
python manage.py update_rating_statistics --item-id item-uuid

# Batch processing
python manage.py update_rating_statistics --batch-size 50
```

## Signals

The system automatically updates rental item statistics when ratings are created, updated, or deleted through Django signals.

## Admin Interface

Enhanced admin interface with:
- Filtering by rating, verification status, reports
- Search functionality
- Read-only fields for system-managed data
- Organized field sets

## Error Handling

### Common Error Responses
- `400` - Validation errors
- `401` - Authentication required
- `403` - Permission denied
- `404` - Resource not found
- `429` - Rate limit exceeded

### Validation Rules
- Rating must be between 1-5
- Users can only rate each item once
- Item must exist before rating
- Comments are optional but recommended

## Security Features

- Authentication required for all endpoints
- User can only edit their own ratings
- Rate limiting to prevent abuse
- Input validation and sanitization
- SQL injection protection through ORM

## Monitoring & Analytics

### Key Metrics to Monitor
- API response times
- Error rates
- Most popular filtering combinations
- Rating distribution trends
- User engagement with helpful votes

### Logging
- Rating creation/deletion events
- Statistics update operations
- Error logging for debugging
- Performance metrics

## Future Enhancements

### Planned Features
- Rating sentiment analysis
- Automated spam detection
- Rating photo attachments
- Rating reply system
- Advanced analytics dashboard
- Export functionality

### Performance Improvements
- Redis caching for statistics
- Database query optimization
- Background task processing
- CDN integration for static data

## Support & Documentation

- API Documentation: `API_DOCUMENTATION.md`
- Test Suite: `test_enhanced_features.py`
- Management Commands: `management/commands/`
- Admin Interface: `admin.py`

## Contributing

1. Follow Django coding standards
2. Write tests for new features
3. Update documentation
4. Test performance impact
5. Ensure backward compatibility

## License

This system is part of the TalentSearch platform and follows the same licensing terms. 