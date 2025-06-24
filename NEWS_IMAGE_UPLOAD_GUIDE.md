# News Creation with Direct Image Upload

This guide explains how to create news articles with direct image upload in a single API call.

## Features

✅ **Single API Call**: Create news with images in one request  
✅ **Multiple Images**: Upload up to 10 images per news article  
✅ **Image Captions**: Optional captions for each image  
✅ **Validation**: Comprehensive image validation (size, format, dimensions)  
✅ **Backward Compatible**: Still supports the old two-step process  

## API Endpoint

```
POST /api/news/
```

## Authentication
- **Required**: Admin authentication
- **Headers**: `Authorization: Bearer <token>`

## Request Format

### Content Type
```
Content-Type: multipart/form-data
```

### Form Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | ✅ Yes | News title (max 255 chars) |
| `content` | string | ✅ Yes | News content (10-50,000 chars) |
| `status` | string | ❌ No | `draft`, `published`, or `archived` (default: `draft`) |
| `images` | file[] | ❌ No | Array of image files (max 10) |
| `image_captions` | string[] | ❌ No | Array of captions (must match image count) |

### Supported Image Formats
- **File Types**: JPG, JPEG, PNG, GIF, WebP
- **Max Size**: 5MB per image
- **Max Dimensions**: 1920×1080 pixels

## Example Usage

### 1. JavaScript/Fetch API
```javascript
const formData = new FormData();
formData.append('title', 'Breaking News');
formData.append('content', 'This is the news content...');
formData.append('status', 'published');

// Add multiple images
formData.append('images', imageFile1);
formData.append('images', imageFile2);

// Add captions (optional)
formData.append('image_captions', 'Caption for first image');
formData.append('image_captions', 'Caption for second image');

const response = await fetch('/api/news/', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + token
    },
    body: formData
});

const result = await response.json();
console.log(result);
// Output: { "id": "uuid", "message": "News created successfully.", "images_uploaded": 2 }
```

### 2. Python/Requests
```python
import requests

url = 'http://localhost:8000/api/news/'
headers = {'Authorization': 'Bearer ' + token}

data = {
    'title': 'Breaking News',
    'content': 'This is the news content...',
    'status': 'published',
    'image_captions': ['Caption 1', 'Caption 2']
}

files = [
    ('images', ('image1.jpg', open('image1.jpg', 'rb'), 'image/jpeg')),
    ('images', ('image2.png', open('image2.png', 'rb'), 'image/png')),
]

response = requests.post(url, headers=headers, data=data, files=files)
print(response.json())
```

### 3. cURL
```bash
curl -X POST "http://localhost:8000/api/news/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "title=Breaking News" \
  -F "content=This is the news content..." \
  -F "status=published" \
  -F "images=@image1.jpg" \
  -F "images=@image2.png" \
  -F "image_captions=Caption for first image" \
  -F "image_captions=Caption for second image"
```

## Response Format

### Success Response (201 Created)
```json
{
  "id": "12345678-1234-1234-1234-123456789abc",
  "message": "News created successfully.",
  "images_uploaded": 2
}
```

### Error Response (400 Bad Request)
```json
{
  "images": ["Maximum of 10 images allowed per news article"],
  "image_captions": ["Number of captions must match the number of images"],
  "title": ["This field is required."]
}
```

## Validation Rules

### Images
- **Maximum count**: 10 images per news article
- **File size**: Maximum 5MB per image
- **Dimensions**: Maximum 1920×1080 pixels
- **File types**: JPG, JPEG, PNG, GIF, WebP only

### Captions
- **Length**: Maximum 255 characters per caption
- **Count**: Must match the number of images (if provided)
- **Optional**: Can be omitted entirely

### News Content
- **Title**: 1-255 characters, required
- **Content**: 10-50,000 characters, required
- **Status**: Must be valid choice (draft/published/archived)

## Retrieving News with Images

When retrieving news, images are included in the response:

```json
{
  "id": "12345678-1234-1234-1234-123456789abc",
  "title": "Breaking News",
  "content": "This is the news content...",
  "status": "published",
  "created_by": "admin",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "image_gallery": [
    {
      "id": 1,
      "image": "/media/news_images/image1.jpg",
      "caption": "Caption for first image"
    },
    {
      "id": 2,
      "image": "/media/news_images/image2.png",
      "caption": "Caption for second image"
    }
  ],
  "tags": []
}
```

## Frontend Implementation Tips

### React Example
```jsx
const NewsCreateForm = () => {
  const [files, setFiles] = useState([]);
  const [captions, setCaptions] = useState([]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    
    formData.append('title', title);
    formData.append('content', content);
    formData.append('status', status);
    
    files.forEach(file => formData.append('images', file));
    captions.forEach(caption => formData.append('image_captions', caption));
    
    const response = await fetch('/api/news/', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input type="text" name="title" required />
      <textarea name="content" required />
      <select name="status">
        <option value="draft">Draft</option>
        <option value="published">Published</option>
      </select>
      <input 
        type="file" 
        multiple 
        accept="image/*"
        onChange={(e) => setFiles(Array.from(e.target.files))}
      />
      {/* Caption inputs for each file */}
      <button type="submit">Create News</button>
    </form>
  );
};
```

## Migration Notes

- **Backward Compatibility**: The old two-step process (create news → upload images separately) still works
- **Database**: No migrations required, uses existing models
- **Existing APIs**: All existing endpoints remain unchanged

## Error Handling

Common validation errors and their solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| "Maximum of 10 images allowed" | Too many files | Reduce image count |
| "Number of captions must match" | Caption/image count mismatch | Provide equal captions and images |
| "Image size must be no more than 5MB" | File too large | Compress or resize image |
| "Image dimensions must be no larger than 1920x1080" | Image too large | Resize image |
| "Only jpg, jpeg, png, gif, webp files are allowed" | Invalid format | Convert to supported format | 