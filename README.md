# TalentSearch Platform - Backend

A robust Django-based backend for a talent management and recruitment platform, designed to handle complex user profiles, authentication, and data management.

## 🌟 Core Features

### User Management
- Secure authentication and authorization
- Role-based access control (Admin, Recruiter, Candidate)
- Profile verification system
- Multi-factor authentication support

### Profile Management
- Comprehensive professional profiles
- Identity verification
- Document management
- Media uploads (photos, videos)
- Skills and qualifications tracking

### Location & Contact Management
- Dynamic region and city selection
- Country validation
- Address management
- Emergency contact handling
- Housing status tracking

### Professional Qualifications
- Experience tracking
- Skills assessment
- Work authorization
- Salary expectations
- Availability management
- Work preferences

### Education & Training
- Educational background
- Certifications
- Online courses
- Academic achievements
- Scholarships

### Work Experience
- Employment history
- Project portfolio
- Training records
- Internship tracking
- Reference management

## 🛠️ Technology Stack

### Backend
- Django 4.2+
- Django REST Framework
- PostgreSQL
- Redis (for caching)
- Celery (for async tasks)

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- Redis 6+

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Strawhat404/TalentSearch-Messages.git
cd TalentSearch-Messages
```

2. Set up the backend:
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Load initial data
python manage.py load_choices_data
```

3. Run the development server:
```bash
python manage.py runserver
```

## 📁 Project Structure

```
TalentSearch-Messages/
├── userprofile/          # User profile management
│   ├── models.py        # Database models
│   ├── serializers.py   # API serializers
│   ├── views.py         # API views
│   └── urls.py          # URL routing
├── authentication/       # Auth system
│   ├── models.py        # User models
│   ├── serializers.py   # Auth serializers
│   └── views.py         # Auth views
├── api/                 # API endpoints
│   ├── views.py         # API views
│   └── urls.py          # API routing
├── core/               # Core functionality
│   ├── settings.py     # Django settings
│   └── urls.py         # Main URL routing
├── data/              # JSON data files
│   ├── regions.json   # Region data
│   ├── cities.json    # City data
│   └── countries.json # Country data
└── tests/            # Test suites
```

## 🔒 Security Features

- Input sanitization
- XSS protection
- CSRF protection
- Rate limiting
- Data encryption
- Secure file uploads
- Audit logging

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test userprofile
python manage.py test authentication
```

## 📊 API Documentation

API documentation is available at `/api/docs/` when running the development server.

## 🔄 Development Workflow

1. Create a new branch from development:
```bash
git checkout development
git pull origin development
git checkout -b feature/your-feature-name
```

2. Make your changes and commit:
```bash
git add .
git commit -m "feat: your feature description"
```

3. Push and create a PR:
```bash
git push origin feature/your-feature-name
```

4. Create a Pull Request to the development branch

## 📝 Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Write docstrings for all functions and classes
- Keep functions small and focused
- Use type hints where appropriate

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Backend Team

- Senior Developer: Yoseph Tesfaye(https://www.linkedin.com/in/yosephtesfaye/)
- Senior Developers: Abel Yitages(https://www.linkedin.com/in/abel-yitages-734339236/)
- Senior Developers: Makeda Tsegazeab(https://www.linkedin.com/in/makda-tsegazeab-1b1a02326/)

## 📞 Support

For backend support, email TalentSearchBackend@gmail.com or join our Slack channel #backend-support.

## 🔄 Updates

- Latest update: 3oth may,2025
- Version: 1.0.0
- Status: Development

---

Made with ❤️ by the TalentSearch Backend Team
