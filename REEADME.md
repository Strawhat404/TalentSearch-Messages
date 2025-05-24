# TalentSearch Platform

A Django-based talent search and management platform that connects talent with opportunities.

## 🚀 Quick Start

1. **Clone & Setup**
```bash
git clone <repository-url>
cd TalentSearch-Messages
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment Setup**
Create `.env`:
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/talentsearch
REDIS_URL=redis://localhost:6379/1
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-email-password
```

3. **Database & Run**
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## 🛠️ Tech Stack

- Django 5.2
- Django REST Framework
- PostgreSQL
- Redis
- JWT Authentication
- Render (Deployment)

## 📁 Core Features

- User Authentication & Profiles
- Job Management
- Messaging System
- News Feed
- Advertisements
- User Gallery
- Like & Comment System

## 🔧 Development

- **Settings**: `talentsearch/settings/`
  - `base.py`: Common settings
  - `dev.py`: Development
  - `prod.py`: Production

- **Key Apps**:
  - `authapp`: Authentication
  - `userprofile`: User profiles
  - `jobs`: Job management
  - `messaging`: Messaging system
  - `feed_posts`: News feed
  - `adverts`: Advertisements

## 🚀 Deployment

Deployed on Render with:
- PostgreSQL database
- Redis cache
- WhiteNoise for static files
- Gunicorn server

## 📚 API Docs

- Swagger UI: `/api/schema/swagger-ui/`
- ReDoc: `/api/schema/redoc/`

## 👥 User Roles

- Admin: Full system access
- Staff: Limited admin access
- Regular User: Standard access
- Employer: Job management

## 🔐 Authentication

- Token-based
- JWT
- Session (admin)

## 🧪 Testing

```bash
pytest
```

## 📞 Support

For support, please contact [Your Contact Information]

## 📝 License

[Your License]
