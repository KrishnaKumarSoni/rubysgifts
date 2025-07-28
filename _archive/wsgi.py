#!/usr/bin/env python3
"""
WSGI Entry Point for Ruby's Gifts Flask Application
==================================================

This module serves as the WSGI entry point for production deployment
on platforms like Vercel, Heroku, or other cloud providers.

It properly configures the Flask application for production use with:
- Environment variable loading
- Production-safe configuration
- Error handling and logging
- WSGI-compatible application object

Author: Claude Code Assistant
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

try:
    # Import the Flask application
    from app import app
    
    # Configure for production
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    
    # Override CORS for production if needed
    if 'VERCEL_URL' in os.environ:
        # Running on Vercel - allow the deployment URL
        vercel_url = f"https://{os.environ['VERCEL_URL']}"
        app.config['CORS_ORIGINS'] = [vercel_url]
        logger.info(f"Configured CORS for Vercel deployment: {vercel_url}")
    
    # Validate critical configuration
    if not app.config.get('OPENAI_API_KEY'):
        logger.error("OPENAI_API_KEY not found in environment variables")
        raise ValueError("OPENAI_API_KEY is required for production deployment")
    
    logger.info("Ruby's Gifts Flask application initialized for production")
    logger.info(f"Debug mode: {app.config['DEBUG']}")
    logger.info(f"OpenAI API key configured: {'Yes' if app.config.get('OPENAI_API_KEY') else 'No'}")
    
except Exception as e:
    logger.error(f"Failed to initialize Flask application: {str(e)}")
    raise

# WSGI application object - this is what the WSGI server will call
application = app

# For compatibility with different WSGI servers
if __name__ == "__main__":
    # This block won't be executed in production WSGI deployment
    # but provides a fallback for direct execution
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)