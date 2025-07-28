# Ruby's Gifts - Production Deployment Guide

## WSGI Configuration Overview

This Flask application is now properly configured for production deployment with WSGI support. The key changes include:

### Files Created/Modified

1. **`wsgi.py`** - WSGI entry point for production deployment
2. **`vercel.json`** - Updated Vercel configuration to use WSGI
3. **`app.py`** - Enhanced with production-ready configurations
4. **`.env.example`** - Template for environment variables

## Deployment Steps

### 1. Environment Variables Setup

Create a `.env` file (for local development) or configure environment variables in your deployment platform:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
SECRET_KEY=your_production_secret_key
FLASK_ENV=production
PRODUCTION_URL=https://your-custom-domain.com
```

### 2. Vercel Deployment

The app is configured for Vercel deployment:

```bash
# Deploy to Vercel
vercel --prod

# Or link to existing project
vercel link
vercel --prod
```

**Important**: Make sure to set the `OPENAI_API_KEY` environment variable in your Vercel project settings.

### 3. Other WSGI Platforms

For other platforms (Heroku, Railway, etc.), use the `wsgi.py` file as the entry point:

- **Heroku**: Create a `Procfile` with: `web: gunicorn wsgi:application`
- **Railway**: Point to `wsgi.py` in deployment settings
- **AWS Lambda**: Use `wsgi.application` as the handler

## Key Features

### Production Configurations

- **WSGI Entry Point**: `wsgi.py` serves as the proper WSGI application
- **Environment Detection**: Automatically detects production vs development
- **CORS Configuration**: Supports both local development and production URLs
- **Error Handling**: Comprehensive error handling with proper logging
- **Security**: Debug mode disabled in production

### API Endpoints

- `GET /` - Serves the main application
- `GET /health` - Health check endpoint
- `POST /generate_gifts` - Gift generation API
- Static files served from root directory

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for gift generation |
| `SECRET_KEY` | No | Flask secret key (auto-generated if not set) |
| `FLASK_ENV` | No | Environment (development/production) |
| `VERCEL_URL` | Auto | Set automatically by Vercel |
| `PRODUCTION_URL` | No | Custom domain URL for CORS |

## Testing the Deployment

### 1. Health Check
```bash
curl https://your-deployment-url/health
```

### 2. API Test
```bash
curl -X POST https://your-deployment-url/generate_gifts \
  -H "Content-Type: application/json" \
  -d '{
    "call_them": "buddy",
    "relationship": "best friend",
    "previous_gifts": "chocolate",
    "hate": "spiders",
    "complaints": "traffic",
    "complain_about_them": "always late",
    "budget": "under 500₹",
    "limitations": "eco-friendly"
  }'
```

## Common Issues

### 1. 401 Authentication Errors
- Ensure `OPENAI_API_KEY` is set in production environment
- Check Vercel environment variables section

### 2. CORS Issues
- CORS is configured for common origins
- Add custom domain to `PRODUCTION_URL` if needed

### 3. Import Errors
- Verify all dependencies are in `requirements.txt`
- Ensure Python version compatibility

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file from template
cp .env.example .env
# Edit .env with your OpenAI API key

# Run development server
python app.py

# Or test WSGI locally
python wsgi.py
```

## Security Notes

- Never commit `.env` files to version control
- Use strong `SECRET_KEY` in production
- OpenAI API key should be kept secure
- CORS origins are restricted to known domains
- Input validation and sanitization implemented

The application is now ready for production deployment with proper WSGI configuration!