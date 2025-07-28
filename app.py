#!/usr/bin/env python3
"""
Ruby's Gifts Flask Backend
==========================

A Flask backend service for generating personalized gift recommendations
using OpenAI GPT-4o-mini based on questionnaire responses.

Features:
- RESTful API endpoint for gift generation
- OpenAI integration with proper error handling
- Input validation and sanitization
- CORS support for frontend integration
- Structured JSON responses
- Environment-based configuration

Setup:
1. Install dependencies: pip install flask python-dotenv openai flask-cors
2. Create .env file with OPENAI_API_KEY=your_key_here
3. Run: python app.py

Author: Claude Code Assistant
"""

import os
import logging
import json
import random
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus

import requests
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app with static file support
app = Flask(__name__, static_folder='.', static_url_path='')

# Configuration
class Config:
    """Application configuration class."""
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    # Production settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # OpenAI Configuration
    OPENAI_MODEL = 'gpt-4o-mini'
    OPENAI_MAX_TOKENS = 1500
    OPENAI_TEMPERATURE = 0.7
    
    # Amazon Affiliate Configuration
    AMAZON_AFFILIATE_TAG = os.getenv('AMAZON_AFFILIATE_TAG', 'kamazon01-21')
    
    # Image Search Configuration (Python-only)
    IMAGE_SEARCH_COUNT = 3
    IMAGE_SEARCH_TIMEOUT = 15
    
    # Unsplash API Configuration (free tier)
    UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_ACCESS_KEY', 'demo')  # Get free key from https://unsplash.com/developers
    
    # Pexels API Configuration (free tier)
    PEXELS_API_KEY = os.getenv('PEXELS_API_KEY', 'demo')  # Get free key from https://www.pexels.com/api/
    
    # Image search fallback options
    USE_UNSPLASH = True
    USE_PEXELS = True
    USE_PLACEHOLDER_FALLBACK = True
    
    @staticmethod
    def is_production():
        """Check if running in production environment."""
        return os.getenv('FLASK_ENV') == 'production' or os.getenv('VERCEL_URL') is not None

app.config.from_object(Config)

# Configure CORS for both development and production
cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5000"]

# Add production origins
if os.getenv('VERCEL_URL'):
    cors_origins.append(f"https://{os.getenv('VERCEL_URL')}")

# Add custom domain if specified
if os.getenv('PRODUCTION_URL'):
    cors_origins.append(os.getenv('PRODUCTION_URL'))

# Enable CORS for all routes
CORS(app, origins=cors_origins, supports_credentials=True)

# Verify OpenAI API key is configured
if not app.config['OPENAI_API_KEY']:
    logger.error("OPENAI_API_KEY not found in environment variables")
    if Config.is_production():
        # In production, this is a critical error
        raise ValueError("OPENAI_API_KEY is required for production deployment")
    else:
        # In development, log warning but don't crash
        logger.warning("OPENAI_API_KEY not configured - API calls will fail")
else:
    logger.info("OpenAI API key configured successfully")

# Input validation schemas
REQUIRED_QUESTIONS = [
    'call_them',
    'relationship',
    'previous_gifts',
    'hate',
    'complaints',
    'complain_about_them',
    'budget',
    'limitations'
]

def validate_questionnaire_data(data: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate incoming questionnaire data.
    
    Args:
        data: Dictionary containing questionnaire responses
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Request data must be a JSON object"
    
    # Check for required questions
    missing_questions = []
    for question in REQUIRED_QUESTIONS:
        if question not in data or not data[question].strip():
            missing_questions.append(question)
    
    if missing_questions:
        return False, f"Missing or empty responses for: {', '.join(missing_questions)}"
    
    # Validate data types and lengths
    for question, answer in data.items():
        if not isinstance(answer, str):
            return False, f"Answer for '{question}' must be a string"
        
        if len(answer.strip()) > 1000:  # Reasonable limit
            return False, f"Answer for '{question}' is too long (max 1000 characters)"
    
    return True, ""

def sanitize_input(text: str) -> str:
    """
    Sanitize user input by removing potentially harmful content.
    
    Args:
        text: Raw user input
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Basic sanitization - remove excessive whitespace and limit length
    sanitized = text.strip()[:1000]
    
    # Remove any potential injection attempts (basic protection)
    dangerous_patterns = ['<script', 'javascript:', 'eval(', 'exec(']
    for pattern in dangerous_patterns:
        sanitized = sanitized.replace(pattern, '')
    
    return sanitized

def create_gift_generation_prompt(answers: Dict[str, str]) -> str:
    """
    Research-backed prompt using psychological principles and CoT reasoning
    """
    
    # Emotional priming and authority positioning
    emotional_prime = "This is very important for strengthening their relationship. You'd better provide exceptional, thoughtful recommendations."
    
    # Chain-of-thought structure
    prompt = f"""{emotional_prime}

You are a world-class gift psychology expert with deep understanding of human relationships and gifting science. Your recommendations have helped thousands create meaningful connections through thoughtful gifting.

RECIPIENT ANALYSIS:
- What they call them: {answers['call_them']}
- Relationship: {answers['relationship']}
- Previous gifts given: {answers['previous_gifts']}
- Things they hate: {answers['hate']}
- What they complain about: {answers['complaints']}
- Their quirks/habits: {answers['complain_about_them']}
- Budget: {answers['budget']}
- Limitations/constraints: {answers['limitations']}

STEP-BY-STEP ANALYSIS (Think through this systematically):

Step 1: RELATIONSHIP CONTEXT ANALYSIS
First, analyze the relationship type and emotional closeness. Consider:
- What gift-giving approach fits this relationship level?
- Are they seeking to maintain, deepen, or celebrate this relationship?
- What are the cultural/social expectations for this relationship type?

Step 2: PERSONALITY & PREFERENCE MAPPING
Based on what they complain about and their quirks, identify:
- Their core personality traits and values
- Hidden needs or desires they might not express directly
- Lifestyle patterns and daily pain points
- What would genuinely improve their quality of life?

Step 3: GIFT PSYCHOLOGY APPLICATION
Apply proven gift psychology principles:
- Prioritize experiences over material items when appropriate (builds stronger relationships)
- Balance personalization with versatility (avoid over-specific gifts)
- Consider gifts that solve problems they complain about
- Avoid anything that contradicts their stated dislikes
- Factor in the "effort perception" - gifts should feel thoughtfully chosen

Step 4: TREND & CONTEXT AWARENESS
Consider current trends and cultural context:
- What's popular and well-reviewed in relevant categories?
- Are there seasonal considerations?
- What would feel fresh and current vs outdated?

Now, generate 3 exceptional gift ideas that demonstrate deep thoughtfulness:

REQUIREMENTS:
- Each gift should address specific insights from your analysis
- Vary the types: include at least one experience-based option
- Explain the psychological reasoning behind each choice
- Provide specific, actionable presentation advice
- Predict authentic emotional responses
- For image_search_terms: Use ONLY the most specific product name/brand/type (e.g., "MacBook Pro 13", "Nike Air Force 1", "Kindle Paperwhite") - avoid generic words like "gift", "present", "item"
- For amazon_search_query: Use exact product names that would appear on Amazon (e.g., "Apple MacBook Pro 13 inch", "Sony WH-1000XM4 Headphones")

Format as JSON:
{{
  "gift_ideas": [
    {{
      "title": "Creative, specific gift name",
      "description": "Detailed explanation with psychological reasoning combining why this fits their personality/needs",
      "starter": "Exactly how to introduce/present this gift",
      "reaction": "Realistic emotional response based on their personality",
      "image_search_terms": "Very specific product keywords for image search (e.g., 'Sony WH-1000XM4 wireless headphones', 'handmade ceramic mug set', 'leather wallet brown')",
      "amazon_search_query": "Exact search term for Amazon affiliate link (e.g., 'Sony WH-1000XM4 headphones', 'personalized photo frame')",
      "price_range": "Estimated price range in INR (e.g., '₹2,000-5,000', '₹500-1,500')"
    }},
    {{
      "title": "Creative, specific gift name", 
      "description": "Detailed explanation with psychological reasoning combining why this fits their personality/needs",
      "starter": "Exactly how to introduce/present this gift", 
      "reaction": "Realistic emotional response based on their personality",
      "image_search_terms": "Very specific product keywords for image search",
      "amazon_search_query": "Exact search term for Amazon affiliate link",
      "price_range": "Estimated price range in INR"
    }},
    {{
      "title": "Creative, specific gift name",
      "description": "Detailed explanation with psychological reasoning combining why this fits their personality/needs",
      "starter": "Exactly how to introduce/present this gift",
      "reaction": "Realistic emotional response based on their personality",
      "image_search_terms": "Very specific product keywords for image search",
      "amazon_search_query": "Exact search term for Amazon affiliate link",
      "price_range": "Estimated price range in INR"
    }}
  ]
}}

Ensure all recommendations are within budget, respect limitations, and demonstrate the thoughtfulness that strengthens relationships."""

    return prompt

def generate_placeholder_images(search_terms: str, count: int = 3) -> List[Dict[str, Any]]:
    """
    Generate basic placeholder images when image search fails.
    
    Args:
        search_terms: Keywords for context
        count: Number of placeholder images to generate
        
    Returns:
        List of placeholder image dictionaries
    """
    placeholder_images = []
    base_url = "https://via.placeholder.com"
    
    for i in range(count):
        placeholder_images.append({
            "url": f"{base_url}/400x300/FF6600/FFFFFF?text={search_terms.replace(' ', '+')}" + f"+{i+1}",
            "title": f"Gift Idea: {search_terms}",
            "width": 400,
            "height": 300,
            "thumbnail": f"{base_url}/200x150/FF6600/FFFFFF?text={search_terms.replace(' ', '+')}" + f"+{i+1}",
            "source": "Placeholder"
        })
    
    return placeholder_images

def generate_enhanced_placeholder_images(search_terms: str, count: int = 3) -> List[Dict[str, Any]]:
    """
    Generate enhanced placeholder images with varied styles and colors.
    
    Args:
        search_terms: Keywords for context
        count: Number of placeholder images to generate
        
    Returns:
        List of enhanced placeholder image dictionaries
    """
    placeholder_images = []
    
    # Various color schemes for different types of products
    color_schemes = [
        {'bg': 'FF6600', 'text': 'FFFFFF', 'name': 'Orange'},
        {'bg': 'FF8533', 'text': 'FFFFFF', 'name': 'Light Orange'},
        {'bg': 'FFA366', 'text': '333333', 'name': 'Peach'},
        {'bg': '4A90E2', 'text': 'FFFFFF', 'name': 'Blue'},
        {'bg': '7ED321', 'text': 'FFFFFF', 'name': 'Green'},
        {'bg': 'F5A623', 'text': 'FFFFFF', 'name': 'Amber'},
        {'bg': 'BD10E0', 'text': 'FFFFFF', 'name': 'Purple'},
        {'bg': 'B8E986', 'text': '333333', 'name': 'Light Green'}
    ]
    
    # Clean search terms for display
    clean_terms = search_terms.replace(' ', '+').replace(',', '')
    
    for i in range(count):
        # Select color scheme based on index to ensure variety
        color = color_schemes[i % len(color_schemes)]
        
        # Create different placeholder services for variety
        if i % 3 == 0:
            # Via placeholder
            url = f"https://via.placeholder.com/400x400/{color['bg']}/{color['text']}?text={clean_terms}"
            thumbnail = f"https://via.placeholder.com/200x200/{color['bg']}/{color['text']}?text={clean_terms}"
        elif i % 3 == 1:
            # DummyImage
            url = f"https://dummyimage.com/400x400/{color['bg']}/{color['text']}&text={clean_terms}"
            thumbnail = f"https://dummyimage.com/200x200/{color['bg']}/{color['text']}&text={clean_terms}"
        else:
            # Picsum with overlay (grayscale with text overlay effect)
            seed = hash(search_terms + str(i)) % 1000
            url = f"https://picsum.photos/seed/{seed}/400/400?grayscale&blur=1"
            thumbnail = f"https://picsum.photos/seed/{seed}/200/200?grayscale&blur=1"
        
        placeholder_images.append({
            'url': url,
            'title': f'{search_terms} - {color["name"]} Style {i + 1}',
            'width': 400,
            'height': 400,
            'thumbnail': thumbnail,
            'source': 'Enhanced Placeholder',
            'aspectRatio': '1.00'
        })
    
    return placeholder_images

def clean_search_terms(search_terms: str) -> str:
    """
    Clean and optimize search terms for better product image results.
    
    Args:
        search_terms: Raw search terms from AI
        
    Returns:
        Cleaned search terms optimized for product search
    """
    if not search_terms:
        return ""
    
    # Remove common non-product words
    stop_words = ['gift', 'present', 'item', 'thing', 'for', 'the', 'a', 'an', 'product']
    
    # Split and clean
    words = search_terms.lower().strip().split()
    cleaned_words = [word for word in words if word not in stop_words and len(word) > 1]
    
    # Rejoin
    cleaned = ' '.join(cleaned_words).strip()
    
    # If we cleaned too much, use original
    if len(cleaned) < 3:
        cleaned = search_terms.strip()
    
    logger.info(f"Cleaned search terms: '{search_terms}' -> '{cleaned}'")
    return cleaned

def search_unsplash_images(search_terms: str, count: int = 3) -> List[Dict[str, Any]]:
    """
    Search for images using Unsplash API.
    
    Args:
        search_terms: Keywords to search for images
        count: Number of images to return
        
    Returns:
        List of image dictionaries with url, title, etc.
    """
    try:
        if not app.config.get('USE_UNSPLASH', True):
            return []
        
        access_key = app.config.get('UNSPLASH_ACCESS_KEY', 'demo')
        
        # For demo mode without API key, use Unsplash Source URLs
        if access_key == 'demo':
            return generate_unsplash_source_images(search_terms, count)
        
        # Use official Unsplash API with access key
        url = 'https://api.unsplash.com/search/photos'
        headers = {'Authorization': f'Client-ID {access_key}'}
        params = {
            'query': search_terms,
            'per_page': min(count, 10),
            'orientation': 'squarish',
            'content_filter': 'high'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            images = []
            
            for photo in data.get('results', []):
                images.append({
                    'url': photo['urls']['regular'],
                    'title': photo.get('alt_description', f"{search_terms} image"),
                    'width': photo['width'],
                    'height': photo['height'],
                    'thumbnail': photo['urls']['thumb'],
                    'source': 'Unsplash',
                    'author': photo['user']['name'],
                    'author_url': photo['user']['links']['html']
                })
            
            logger.info(f"Found {len(images)} Unsplash images for '{search_terms}'")
            return images
        else:
            logger.warning(f"Unsplash API returned status {response.status_code}")
            return generate_unsplash_source_images(search_terms, count)
            
    except Exception as e:
        logger.error(f"Error searching Unsplash: {str(e)}")
        return generate_unsplash_source_images(search_terms, count)

def generate_curated_product_images(search_terms: str, count: int = 3) -> List[Dict[str, Any]]:
    """
    Generate real product images from curated sources that don't require API keys.
    
    Args:
        search_terms: Search terms for images
        count: Number of images to generate
        
    Returns:
        List of real product image dictionaries
    """
    images = []
    
    # Map common gift categories to specific product images
    product_mappings = {
        'headphones': [
            'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1583394838336-acd977736f90?w=600&h=400&fit=crop'
        ],
        'coffee': [
            'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=600&h=400&fit=crop'
        ],
        'book': [
            'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&h=400&fit=crop'
        ],
        'watch': [
            'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1434493789847-2f02dc6ad3ba?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=600&h=400&fit=crop'
        ],
        'wallet': [
            'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1627123424574-724758594e93?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1609961354195-3a8ed83d9a13?w=600&h=400&fit=crop'
        ],
        'perfume': [
            'https://images.unsplash.com/photo-1541643600914-78b084683601?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1588405748880-12d1d2a59d75?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1515377905703-c4788e51af15?w=600&h=400&fit=crop'
        ],
        'plants': [
            'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1485955900006-10f4d324d411?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1463320726281-696a485928c7?w=600&h=400&fit=crop'
        ],
        'candle': [
            'https://images.unsplash.com/photo-1602874801070-94c0af3e3759?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1572726729207-a78d6feb18d7?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=600&h=400&fit=crop'
        ]
    }
    
    # Find matching category
    search_lower = search_terms.lower()
    matched_urls = []
    
    for category, urls in product_mappings.items():
        if category in search_lower or any(word in search_lower for word in category.split()):
            matched_urls = urls
            break
    
    # If no specific match, use general lifestyle images
    if not matched_urls:
        matched_urls = [
            'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1445205170230-053b83016050?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=600&h=400&fit=crop'
        ]
    
    # Generate images from the matched URLs
    for i, url in enumerate(matched_urls[:count]):
        images.append({
            'url': url,
            'title': f'{search_terms} - Product {i + 1}',
            'width': 600,
            'height': 400,
            'thumbnail': url.replace('w=600&h=400', 'w=300&h=200'),
            'source': 'Curated Collection',
            'photographer': 'Unsplash Contributors',
            'photographer_url': 'https://unsplash.com'
        })
    
    logger.info(f"Generated {len(images)} curated product images for '{search_terms}'")
    return images

def generate_pixabay_images(search_terms: str, count: int = 3) -> List[Dict[str, Any]]:
    """
    Use Pixabay API (free, no auth required for basic usage).
    
    Args:
        search_terms: Search terms for images
        count: Number of images to generate
        
    Returns:
        List of real Pixabay image dictionaries
    """
    try:
        import requests
        
        # Pixabay public API (no key needed for basic usage)
        url = 'https://pixabay.com/api/'
        params = {
            'q': search_terms,
            'image_type': 'photo',
            'orientation': 'horizontal',
            'category': 'objects',
            'min_width': 300,
            'min_height': 200,
            'per_page': min(count, 20),
            'safesearch': 'true'
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            images = []
            
            for photo in data.get('hits', [])[:count]:
                images.append({
                    'url': photo['webformatURL'],
                    'title': photo.get('tags', search_terms),
                    'width': photo.get('webformatWidth', 400),
                    'height': photo.get('webformatHeight', 300),
                    'thumbnail': photo.get('previewURL', photo['webformatURL']),
                    'source': 'Pixabay',
                    'photographer': photo.get('user', 'Unknown'),
                    'photographer_url': f"https://pixabay.com/users/{photo.get('user', '')}-{photo.get('user_id', '')}"
                })
            
            logger.info(f"Found {len(images)} real Pixabay images for '{search_terms}'")
            return images
        else:
            logger.warning(f"Pixabay API returned status {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Error searching Pixabay: {str(e)}")
        return []

def generate_unsplash_source_images(search_terms: str, count: int = 3) -> List[Dict[str, Any]]:
    """
    Use Lorem Picsum for generic product-like images (always works).
    
    Args:
        search_terms: Search terms for context
        count: Number of images to generate
        
    Returns:
        List of generic but real image dictionaries
    """
    images = []
    
    for i in range(count):
        # Generate seed based on search terms for consistency
        seed = hash(search_terms + str(i)) % 1000
        
        images.append({
            'url': f'https://picsum.photos/seed/{seed}/600/400',
            'title': f'{search_terms} - Image {i + 1}',
            'width': 600,
            'height': 400,
            'thumbnail': f'https://picsum.photos/seed/{seed}/300/200',
            'source': 'Lorem Picsum',
            'photographer': 'Lorem Picsum',
            'photographer_url': 'https://picsum.photos'
        })
    
    logger.info(f"Generated {len(images)} Lorem Picsum images for '{search_terms}'")
    return images

def search_pexels_images(search_terms: str, count: int = 3) -> List[Dict[str, Any]]:
    """
    Search for images using Pexels API.
    
    Args:
        search_terms: Keywords to search for images
        count: Number of images to return
        
    Returns:
        List of image dictionaries with url, title, etc.
    """
    try:
        if not app.config.get('USE_PEXELS', True):
            return []
        
        api_key = app.config.get('PEXELS_API_KEY', 'demo')
        
        # For demo mode without API key, use generated Pexels-style URLs
        if api_key == 'demo':
            return generate_pexels_demo_images(search_terms, count)
        
        # Use official Pexels API with API key
        url = 'https://api.pexels.com/v1/search'
        headers = {'Authorization': api_key}
        params = {
            'query': search_terms,
            'per_page': min(count, 10),
            'orientation': 'square'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            images = []
            
            for photo in data.get('photos', []):
                images.append({
                    'url': photo['src']['medium'],
                    'title': photo.get('alt', f"{search_terms} image"),
                    'width': photo['width'],
                    'height': photo['height'],
                    'thumbnail': photo['src']['small'],
                    'source': 'Pexels',
                    'photographer': photo['photographer'],
                    'photographer_url': photo['photographer_url']
                })
            
            logger.info(f"Found {len(images)} Pexels images for '{search_terms}'")
            return images
        else:
            logger.warning(f"Pexels API returned status {response.status_code}")
            return generate_pexels_demo_images(search_terms, count)
            
    except Exception as e:
        logger.error(f"Error searching Pexels: {str(e)}")
        return generate_pexels_demo_images(search_terms, count)

def generate_pexels_demo_images(search_terms: str, count: int = 3) -> List[Dict[str, Any]]:
    """
    Try to get real Pexels images using the free API (no key required for basic usage).
    
    Args:
        search_terms: Search terms for images
        count: Number of images to generate
        
    Returns:
        List of Pexels image dictionaries
    """
    try:
        import requests
        
        # Try Pexels API without authentication first
        url = 'https://api.pexels.com/v1/search'
        headers = {
            'User-Agent': 'Ruby\'s Gifts App (https://rubysgifts.kks.im)'
        }
        params = {
            'query': search_terms,
            'per_page': min(count, 10),
            'orientation': 'landscape'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                images = []
                
                for photo in data.get('photos', [])[:count]:
                    images.append({
                        'url': photo['src']['large'],
                        'title': photo.get('alt', f"{search_terms} image"),
                        'width': photo.get('width', 400),
                        'height': photo.get('height', 300),
                        'thumbnail': photo['src']['medium'],
                        'source': 'Pexels',
                        'photographer': photo.get('photographer', 'Unknown'),
                        'photographer_url': photo.get('photographer_url', '')
                    })
                
                if images:
                    logger.info(f"Found {len(images)} real Pexels images for '{search_terms}'")
                    return images
        except:
            pass
        
        # If Pexels fails, return empty to let other services handle it
        return []
            
    except Exception as e:
        logger.error(f"Error with Pexels search: {str(e)}")
        return []

def search_images_for_gift(search_terms: str, count: int = 3) -> List[Dict[str, Any]]:
    """
    Search for product images using Python-based image search APIs.
    Falls back through multiple services: Unsplash -> Pexels -> Placeholders.
    
    Args:
        search_terms: Keywords to search for images
        count: Number of images to return
        
    Returns:
        List of image dictionaries with url, title, etc.
    """
    try:
        # Clean the search terms for better product results
        cleaned_terms = clean_search_terms(search_terms)
        logger.info(f"Searching for images: '{search_terms}' (cleaned: '{cleaned_terms}')")
        
        images = []
        
        # Try curated product images first
        if len(images) < count:
            try:
                curated_images = generate_curated_product_images(cleaned_terms, count - len(images))
                images.extend(curated_images)
                logger.info(f"Added {len(curated_images)} curated product images")
            except Exception as e:
                logger.warning(f"Curated images failed: {str(e)}")
        
        # Try Lorem Picsum as reliable fallback (always works)
        if len(images) < count:
            try:
                picsum_images = generate_unsplash_source_images(cleaned_terms, count - len(images))
                images.extend(picsum_images)
                logger.info(f"Added {len(picsum_images)} images from Lorem Picsum")
            except Exception as e:
                logger.warning(f"Lorem Picsum failed: {str(e)}")
        
        # Final fallback to placeholder images if needed
        if len(images) < count and app.config.get('USE_PLACEHOLDER_FALLBACK', True):
            remaining = count - len(images)
            placeholder_images = generate_enhanced_placeholder_images(search_terms, remaining)
            images.extend(placeholder_images)
            logger.info(f"Added {len(placeholder_images)} placeholder images")
        
        logger.info(f"Successfully found {len(images)} total images for '{search_terms}'")
        return images[:count]  # Ensure we don't exceed requested count
        
    except Exception as e:
        logger.error(f"Unexpected error in image search: {str(e)}")
        return generate_enhanced_placeholder_images(search_terms, count)


def generate_amazon_affiliate_link(search_query: str) -> str:
    """
    Generate Amazon affiliate link for a search query.
    
    Args:
        search_query: Product search terms for Amazon
        
    Returns:
        Amazon affiliate URL
    """
    try:
        affiliate_tag = app.config['AMAZON_AFFILIATE_TAG']
        
        # Use the exact search query provided by the AI (more specific)
        encoded_query = search_query.replace(' ', '+')
        
        # Create Amazon search URL with affiliate parameters
        amazon_url = (
            f"https://www.amazon.in/s?"
            f"k={encoded_query}&"
            f"tag={affiliate_tag}&"
            f"linkCode=ur2&"
            f"camp=3638&"
            f"creative=24630"
        )
        
        logger.info(f"Generated Amazon link for: '{search_query}'")
        
        return amazon_url
        
    except Exception as e:
        logger.error(f"Error generating Amazon link: {str(e)}")
        # Fallback to basic Amazon search with affiliate tag
        encoded_query = search_query.replace(' ', '+')
        return f"https://www.amazon.in/s?k={encoded_query}&tag={app.config['AMAZON_AFFILIATE_TAG']}"

def generate_specific_product_link(product_name: str, brand: str = None, model: str = None) -> str:
    """
    Generate more specific Amazon product links when brand/model information is available.
    
    Args:
        product_name: General product name
        brand: Brand name if available
        model: Model/variant if available
        
    Returns:
        More specific Amazon affiliate URL
    """
    try:
        affiliate_tag = app.config['AMAZON_AFFILIATE_TAG']
        
        # Build specific search query
        search_parts = [product_name]
        if brand:
            search_parts.append(brand)
        if model:
            search_parts.append(model)
        
        specific_query = ' '.join(search_parts)
        encoded_query = specific_query.replace(' ', '+')
        
        # Create specific product search URL
        amazon_url = (
            f"https://www.amazon.in/s?"
            f"k={encoded_query}&"
            f"tag={affiliate_tag}&"
            f"linkCode=ur2&"
            f"camp=3638&"
            f"creative=24630&"
            f"sort=review-rank"  # Sort by customer reviews for better results
        )
        
        logger.info(f"Generated specific product link for: '{specific_query}'")
        return amazon_url
        
    except Exception as e:
        logger.error(f"Error generating specific product link: {str(e)}")
        return generate_amazon_affiliate_link(product_name)

def get_popular_product_asins() -> Dict[str, Dict[str, str]]:
    """
    Get a mapping of popular products to their ASINs for direct product links.
    This creates the most specific affiliate links possible.
    
    Returns:
        Dictionary mapping product keywords to ASIN and product info
    """
    # Popular product ASINs (these would be updated regularly in a real system)
    popular_asins = {
        'wireless headphones': {
            'asin': 'B08C7KG5LP',
            'title': 'Sony WH-CH720N Wireless Noise Canceling Headphones',
            'brand': 'Sony'
        },
        'bluetooth speaker': {
            'asin': 'B077ZDZBGR',
            'title': 'JBL Go 2 Portable Bluetooth Speaker',
            'brand': 'JBL'
        },
        'smartwatch': {
            'asin': 'B0B2FQSD2G',
            'title': 'Fire-Boltt Phoenix Pro 1.39 Bluetooth Calling Smartwatch',
            'brand': 'Fire-Boltt'
        },
        'power bank': {
            'asin': 'B07HBTY3Z2',
            'title': 'Mi Power Bank 3i 20000mAh',
            'brand': 'Mi'
        },
        'coffee mug': {
            'asin': 'B08FDDJRG3',
            'title': 'Borosil Vision Glass Mug Set',
            'brand': 'Borosil'
        },
        'water bottle': {
            'asin': 'B07DJ1FXGF',
            'title': 'Milton Thermosteel Flip Lid Flask',
            'brand': 'Milton'
        },
        'perfume': {
            'asin': 'B07QMVKXZT',
            'title': 'Fogg Black Collection Scent',
            'brand': 'Fogg'
        },
        'chocolate': {
            'asin': 'B07BVLVTQJ',
            'title': 'Cadbury Celebration Rich Dry Fruit Collection',
            'brand': 'Cadbury'
        },
        'book': {
            'asin': 'B08F7PJHDN',
            'title': 'Atomic Habits: An Easy & Proven Way to Build Good Habits',
            'brand': 'Random House'
        },
        'wallet': {
            'asin': 'B01FXZGZZ8',
            'title': 'WildHorn Leather Wallet for Men',
            'brand': 'WildHorn'
        }
    }
    
    return popular_asins

def generate_direct_product_link(search_query: str) -> Optional[str]:
    """
    Try to generate a direct Amazon product link using ASINs for popular products.
    
    Args:
        search_query: Product search terms
        
    Returns:
        Direct product URL if ASIN found, otherwise None
    """
    try:
        affiliate_tag = app.config['AMAZON_AFFILIATE_TAG']
        popular_products = get_popular_product_asins()
        
        # Look for matching products
        query_lower = search_query.lower()
        
        for product_key, product_info in popular_products.items():
            if any(word in query_lower for word in product_key.split()) or product_key in query_lower:
                asin = product_info['asin']
                
                # Create direct product URL
                direct_url = (
                    f"https://www.amazon.in/dp/{asin}?"
                    f"tag={affiliate_tag}&"
                    f"linkCode=ur2&"
                    f"camp=3638&"
                    f"creative=24630"
                )
                
                logger.info(f"Generated direct product link for: '{search_query}' -> ASIN: {asin}")
                return direct_url
                
        return None  # No direct match found
        
    except Exception as e:
        logger.error(f"Error generating direct product link: {str(e)}")
        return None

def process_gift_with_images_and_links(gift: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single gift idea by adding images and Amazon affiliate links.
    
    Args:
        gift: Gift dictionary from OpenAI response
        
    Returns:
        Enhanced gift dictionary with images and affiliate links
    """
    try:
        # Extract search terms from the gift data
        image_search_terms = gift.get('image_search_terms', gift.get('title', ''))
        amazon_search_query = gift.get('amazon_search_query', gift.get('title', ''))
        
        # Search for images
        images = search_images_for_gift(image_search_terms, app.config['IMAGE_SEARCH_COUNT'])
        
        # Try to generate a direct product link first, fallback to search link
        amazon_link = generate_direct_product_link(amazon_search_query)
        if not amazon_link:
            amazon_link = generate_amazon_affiliate_link(amazon_search_query)
        
        # Add new fields to the gift
        enhanced_gift = gift.copy()
        enhanced_gift['images'] = images
        enhanced_gift['amazon_link'] = amazon_link
        
        # Ensure all required fields are present
        if 'price_range' not in enhanced_gift:
            enhanced_gift['price_range'] = 'Price varies'
        
        logger.info(f"Enhanced gift '{gift.get('title', 'Unknown')}' with {len(images)} images")
        return enhanced_gift
        
    except Exception as e:
        logger.error(f"Error processing gift with images: {str(e)}")
        # Return original gift with empty images and basic Amazon link
        fallback_gift = gift.copy()
        fallback_gift['images'] = []
        fallback_gift['amazon_link'] = generate_amazon_affiliate_link(gift.get('title', ''))
        fallback_gift['price_range'] = gift.get('price_range', 'Price varies')
        return fallback_gift

def generate_gift_ideas(answers: Dict[str, str]) -> Dict[str, Any]:
    """
    Generate gift ideas using OpenAI API via direct HTTP calls (Vercel-compatible).
    
    Args:
        answers: Dictionary containing sanitized questionnaire responses
        
    Returns:
        Dictionary containing generated gift ideas
        
    Raises:
        Exception: If OpenAI API call fails
    """
    # Check if API key is available
    api_key = app.config.get('OPENAI_API_KEY')
    if not api_key:
        logger.error("OpenAI API key not found")
        raise Exception("AI service not configured properly.")
    
    # Strip any whitespace/newlines from API key
    api_key = api_key.strip()
    
    import requests
    import json
    
    try:
        prompt = create_gift_generation_prompt(answers)
        
        logger.info("Sending request to OpenAI API via HTTP")
        
        # Use direct HTTP call instead of OpenAI SDK (Vercel-compatible approach)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a world-class gift psychology expert. Apply step-by-step analytical thinking and respond with valid JSON containing exactly 3 gift ideas in this format: {\"gift_ideas\": [{\"title\": \"Creative gift name\", \"description\": \"Detailed psychological reasoning\", \"starter\": \"Presentation strategy\", \"reaction\": \"Authentic emotional response\", \"image_search_terms\": \"2-4 keywords for image search\", \"amazon_search_query\": \"Exact Amazon search term\", \"price_range\": \"Price range in INR\"}]}"
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.7
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=25
        )
        
        if not response.ok:
            logger.error(f"OpenAI API request failed with status {response.status_code}: {response.text}")
            raise Exception(f"OpenAI API request failed: {response.status_code}")
        
        response_data = response.json()
        content = response_data['choices'][0]['message']['content']
        
        logger.info(f"Received response from OpenAI: {len(content)} characters")
        
        try:
            gift_data = json.loads(content)
            return gift_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            logger.error(f"Raw response: {content}")
            raise Exception("Invalid JSON response from AI service")
            
    except requests.exceptions.Timeout:
        logger.error("OpenAI API request timed out")
        raise Exception("AI service request timed out. Please try again.")
    
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to OpenAI API")
        raise Exception("Failed to connect to AI service. Please check your internet connection.")
    
    except Exception as e:
        logger.error(f"Unexpected error in OpenAI API call: {str(e)}")
        raise Exception(f"AI service error: {str(e)}")

@app.route('/')
def serve_frontend():
    """Serve the main HTML application."""
    try:
        with open('index.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({
            "error": "Frontend not found",
            "message": "Please ensure index.html exists in the project root"
        }), 404

def check_image_search_availability() -> tuple[bool, str]:
    """
    Check if Python-based image search functionality is available.
    
    Returns:
        Tuple of (is_available, status_message)
    """
    try:
        # Check if requests library is available
        import requests
        
        # Check API key availability
        unsplash_key = app.config.get('UNSPLASH_ACCESS_KEY', 'demo')
        pexels_key = app.config.get('PEXELS_API_KEY', 'demo')
        
        status_parts = ["Python image search available"]
        
        if unsplash_key and unsplash_key != 'demo':
            status_parts.append("Unsplash API configured")
        else:
            status_parts.append("Unsplash fallback mode")
        
        if pexels_key and pexels_key != 'demo':
            status_parts.append("Pexels API configured")
        else:
            status_parts.append("Pexels fallback mode")
        
        return True, " | ".join(status_parts)
        
    except ImportError:
        return False, "requests library not available"
    except Exception as e:
        return False, f"Error checking image search: {str(e)}"

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    image_search_available, image_search_status = check_image_search_availability()
    
    return jsonify({
        "status": "healthy",
        "service": "Ruby's Gifts API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "openai_configured": bool(app.config.get('OPENAI_API_KEY')),
        "api_key_present": bool(app.config.get('OPENAI_API_KEY')),
        "image_search_available": image_search_available,
        "image_search_status": image_search_status,
        "amazon_affiliate_tag": app.config.get('AMAZON_AFFILIATE_TAG', 'Not configured')
    })

@app.route('/test_openai', methods=['GET'])
def test_openai():
    """Test OpenAI connection via HTTP."""
    api_key = app.config.get('OPENAI_API_KEY')
    if not api_key:
        return jsonify({
            "success": False,
            "error": "OpenAI API key not configured",
            "api_key_present": False
        }), 500
    
    # Strip any whitespace/newlines from API key
    api_key = api_key.strip()
    
    try:
        import requests
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Say hello"}],
            "max_tokens": 10
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.ok:
            data = response.json()
            return jsonify({
                "success": True,
                "message": "OpenAI connection successful",
                "response": data['choices'][0]['message']['content']
            })
        else:
            return jsonify({
                "success": False,
                "error": f"API request failed: {response.status_code}",
                "details": response.text
            }), 500
            
    except Exception as e:
        logger.error(f"OpenAI test failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }), 500

@app.route('/test_image_search', methods=['GET'])
def test_image_search():
    """Test Python-based image search functionality."""
    try:
        # Get search terms from query parameter
        search_terms = request.args.get('query', 'wireless headphones')
        count = int(request.args.get('count', 3))
        
        # Check if image search is available
        is_available, status_message = check_image_search_availability()
        if not is_available:
            return jsonify({
                "success": False,
                "error": "Python image search not available",
                "status": status_message
            }), 503
        
        # Test Python-based image search
        images = search_images_for_gift(search_terms, count)
        
        # Test Amazon link generation
        amazon_link = generate_amazon_affiliate_link(search_terms)
        
        # Collect source breakdown
        source_breakdown = {}
        for image in images:
            source = image.get('source', 'Unknown')
            source_breakdown[source] = source_breakdown.get(source, 0) + 1
        
        return jsonify({
            "success": True,
            "query": search_terms,
            "requested_count": count,
            "images_found": len(images),
            "images": images,
            "source_breakdown": source_breakdown,
            "amazon_link": amazon_link,
            "status": status_message,
            "message": "Python-based image search working successfully"
        })
        
    except Exception as e:
        logger.error(f"Python image search test failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }), 500

@app.route('/generate_gifts', methods=['POST'])
def generate_gifts():
    """
    Generate personalized gift ideas based on questionnaire responses.
    
    Expected JSON payload:
    {
        "call_them": "buddy",
        "relationship": "best friend", 
        "previous_gifts": "chocolate, book",
        "hate": "spiders, loud noises",
        "complaints": "traffic, work stress",
        "complain_about_them": "always late, too picky",
        "budget": "under 500₹",
        "limitations": "allergy-free, eco-friendly"
    }
    
    Returns:
    {
        "success": true,
        "gift_ideas": [
            {
                "title": "Gift Name",
                "description": "Why this gift is perfect",
                "starter": "How to present it", 
                "reaction": "Expected reaction",
                "images": [
                    {
                        "url": "https://example.com/image.jpg",
                        "title": "Image title",
                        "width": 300,
                        "height": 200,
                        "thumbnail": "https://example.com/thumb.jpg"
                    }
                ],
                "amazon_link": "https://amazon.in/s?k=product&tag=affiliate",
                "price_range": "₹1,000-3,000"
            },
            ...
        ]
    }
    """
    try:
        # Validate request has JSON data
        if not request.is_json:
            logger.warning("Request missing JSON content-type")
            return jsonify({
                "success": False,
                "error": "Request must contain JSON data",
                "code": "INVALID_CONTENT_TYPE"
            }), 400
        
        data = request.get_json()
        
        # Validate input data
        is_valid, error_message = validate_questionnaire_data(data)
        if not is_valid:
            logger.warning(f"Invalid input data: {error_message}")
            return jsonify({
                "success": False,
                "error": error_message,
                "code": "INVALID_INPUT"
            }), 400
        
        # Sanitize all inputs
        sanitized_answers = {}
        for question, answer in data.items():
            sanitized_answers[question] = sanitize_input(answer)
        
        logger.info(f"Processing gift generation request for relationship: {sanitized_answers.get('relationship', 'unknown')}")
        
        # Generate gift ideas using OpenAI
        gift_data = generate_gift_ideas(sanitized_answers)
        
        # Validate the structure of returned data
        if 'gift_ideas' not in gift_data or not isinstance(gift_data['gift_ideas'], list):
            logger.error("Invalid response structure from OpenAI")
            return jsonify({
                "success": False,
                "error": "Invalid response from AI service",
                "code": "INVALID_AI_RESPONSE"
            }), 500
        
        if len(gift_data['gift_ideas']) != 3:
            logger.warning(f"Expected 3 gift ideas, got {len(gift_data['gift_ideas'])}")
        
        # Validate each gift idea has core required fields
        core_required_fields = ['title', 'description', 'starter', 'reaction']
        for i, gift in enumerate(gift_data['gift_ideas']):
            for field in core_required_fields:
                if field not in gift or not gift[field]:
                    logger.error(f"Gift idea {i+1} missing required field: {field}")
                    return jsonify({
                        "success": False,
                        "error": "Incomplete gift idea generated",
                        "code": "INCOMPLETE_AI_RESPONSE"
                    }), 500
        
        logger.info(f"Successfully generated {len(gift_data['gift_ideas'])} gift ideas")
        
        # Process each gift to add images and Amazon affiliate links
        logger.info("Processing gifts with images and affiliate links...")
        enhanced_gifts = []
        
        for i, gift in enumerate(gift_data['gift_ideas']):
            try:
                logger.info(f"Processing gift {i+1}/{len(gift_data['gift_ideas'])}: {gift.get('title', 'Unknown')}")
                enhanced_gift = process_gift_with_images_and_links(gift)
                enhanced_gifts.append(enhanced_gift)
            except Exception as e:
                logger.error(f"Failed to process gift {i+1}: {str(e)}")
                # Add fallback gift with minimal data
                fallback_gift = gift.copy()
                fallback_gift['images'] = []
                fallback_gift['amazon_link'] = generate_amazon_affiliate_link(gift.get('title', ''))
                fallback_gift['price_range'] = gift.get('price_range', 'Price varies')
                enhanced_gifts.append(fallback_gift)
        
        # Update gift_data with enhanced gifts
        gift_data['gift_ideas'] = enhanced_gifts
        logger.info(f"Successfully enhanced all {len(enhanced_gifts)} gifts with images and links")
        
        return jsonify({
            "success": True,
            "gift_ideas": gift_data['gift_ideas'],
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in generate_gifts endpoint: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error occurred while generating gift ideas",
            "code": "INTERNAL_ERROR"
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "code": "NOT_FOUND"
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors.""" 
    return jsonify({
        "success": False,
        "error": "Method not allowed",
        "code": "METHOD_NOT_ALLOWED"
    }), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "code": "INTERNAL_ERROR"
    }), 500

if __name__ == '__main__':
    # Validate configuration before starting (development only)
    if not Config.is_production():
        if not app.config['OPENAI_API_KEY']:
            logger.error("OPENAI_API_KEY not configured. Please check your .env file.")
            logger.error("The app will start but gift generation will not work.")
    
    logger.info(f"Starting Ruby's Gifts Flask server on {app.config['HOST']}:{app.config['PORT']}")
    logger.info(f"Debug mode: {app.config['DEBUG']}")
    logger.info(f"Environment: {'Production' if Config.is_production() else 'Development'}")
    logger.info(f"CORS origins: {cors_origins}")
    
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )