# RealNaijaGist

A modern Nigerian news and entertainment platform built with Django.

## Features

- **News Management**: Create, edit, and publish news articles
- **Category System**: Organize content by categories
- **User Authentication**: Secure login and registration system
- **Admin Dashboard**: Comprehensive content management interface
- **Responsive Design**: Mobile-first, modern UI
- **SEO Optimized**: Meta tags, sitemaps, and structured data
- **Image Optimization**: WebP support and CDN integration
- **Analytics**: View tracking and engagement metrics
- **Carousel Slides**: Featured content showcase
- **Search Functionality**: Full-text search across content

## Tech Stack

- **Backend**: Django 5.x
- **Database**: MySQL/PostgreSQL (production), SQLite (development)
- **Frontend**: HTML5, CSS3, JavaScript, HTMX
- **Image Storage**: Cloudinary CDN
- **Styling**: Custom CSS with responsive design
- **Deployment**: cPanel with GitHub Actions

## Prerequisites

- Python 3.8+
- MySQL/PostgreSQL (for production)
- Cloudinary account (optional)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd realnaijagist
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

## Environment Variables

Create a `.env` file with the following variables:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=3306

# Cloudinary Configuration (Optional)
USE_CLOUDINARY=False
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
CONTACT_EMAIL=your-email@gmail.com
```

## Project Structure

```
realnaijagist/
├── realnaijagist/          # Django project settings
├── news/                   # Main news application
│   ├── models.py          # Database models
│   ├── views.py           # View logic
│   ├── admin.py           # Admin interface
│   └── urls.py            # URL routing
├── templates/              # HTML templates
├── static/                 # CSS, JS, images
├── media/                  # User-uploaded files
├── logs/                   # Application logs
└── manage.py              # Django management script
```

## Key Models

- **Post**: News articles with rich content
- **Category**: Content organization
- **CarouselSlide**: Featured content slides
- **Comment**: User comments on posts
- **PostView**: Analytics tracking
- **NewsletterSubscriber**: Email subscriptions

## Admin Features

- Content management dashboard
- User management
- Analytics overview
- Image optimization tools
- SEO management

## Deployment

The project includes GitHub Actions for automated deployment to cPanel:

1. Set up repository secrets:
   - `FTP_SERVER`
   - `FTP_USERNAME`
   - `FTP_PASSWORD`

2. Push to main branch to trigger deployment

## Security Features

- CSRF protection
- XSS prevention
- SQL injection protection
- Secure headers
- HTTPS enforcement (production)
- Environment variable protection

## Performance Optimizations

- Database query optimization
- Image compression and WebP support
- CDN integration
- Caching strategies
- Static file optimization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is proprietary software.

## Support

For support, contact:
- Email: realnaijagist123@gmail.com
- Phone: 08103257774 / 09044661247

## Changelog

### v1.0.0
- Initial release
- News management system
- User authentication
- Admin dashboard
- Responsive design
- SEO optimization
