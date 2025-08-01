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
import uuid
import hashlib
from datetime import datetime, timedelta
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

# Results storage system for URL routing
# In production, this should be moved to a database like Redis or PostgreSQL
results_store = {}

def generate_result_id():
    """Generate a unique ID for results."""
    return str(uuid.uuid4())[:8]  # Short 8-character ID for cleaner URLs

def store_result(questions_answers: dict, gift_ideas: list) -> str:
    """Store results and return a unique ID."""
    result_id = generate_result_id()
    
    # Ensure ID is unique (unlikely collision but handle it)
    while result_id in results_store:
        result_id = generate_result_id()
    
    results_store[result_id] = {
        'id': result_id,
        'questions_answers': questions_answers,
        'gift_ideas': gift_ideas,
        'created_at': datetime.utcnow(),
        'expires_at': datetime.utcnow() + timedelta(days=30)  # Results expire after 30 days
    }
    
    logger.info(f"Stored results with ID: {result_id}")
    return result_id

def get_result(result_id: str) -> Optional[dict]:
    """Retrieve results by ID."""
    result = results_store.get(result_id)
    
    if not result:
        return None
    
    # Check if result has expired
    if datetime.utcnow() > result['expires_at']:
        del results_store[result_id]
        logger.info(f"Expired result {result_id} removed from storage")
        return None
    
    return result

def cleanup_expired_results():
    """Clean up expired results from storage."""
    now = datetime.utcnow()
    expired_ids = [
        result_id for result_id, result_data in results_store.items()
        if now > result_data['expires_at']
    ]
    
    for result_id in expired_ids:
        del results_store[result_id]
        logger.info(f"Cleaned up expired result: {result_id}")
    
    logger.info(f"Cleanup complete. Removed {len(expired_ids)} expired results.")

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

def search_real_product_images(search_terms: str, count: int = 3) -> List[Dict[str, Any]]:
    """
    Search for real product images using multiple free sources and APIs.
    
    Args:
        search_terms: Search terms for images
        count: Number of images to return
        
    Returns:
        List of real product image dictionaries
    """
    images = []
    
    # Method 1: Use ImgBB API (free tier, no key required for basic usage)
    try:
        if len(images) < count:
            imgbb_images = search_imgbb_images(search_terms, count - len(images))
            images.extend(imgbb_images)
    except:
        pass
    
    # Method 2: Use Pixabay with public endpoints
    try:
        if len(images) < count:
            pixabay_images = search_pixabay_public(search_terms, count - len(images))
            images.extend(pixabay_images)
    except:
        pass
    
    # Method 3: Use curated real product URLs (Unsplash direct links)
    try:
        if len(images) < count:
            curated_images = get_curated_product_images(search_terms, count - len(images))
            images.extend(curated_images)
    except:
        pass
    
    # Method 4: Use JSONBin API for product images (community driven)
    try:
        if len(images) < count:
            jsonbin_images = search_jsonbin_products(search_terms, count - len(images))
            images.extend(jsonbin_images)
    except:
        pass
    
    logger.info(f"Found {len(images)} real product images for '{search_terms}'")
    return images[:count]

def search_imgbb_images(search_terms: str, count: int = 3) -> List[Dict[str, Any]]:
    """Try ImgBB public galleries for product images."""
    return []  # Placeholder for now

def search_pixabay_public(search_terms: str, count: int = 3) -> List[Dict[str, Any]]:
    """Try public Pixabay endpoints."""
    return []  # Placeholder for now

def search_google_custom_images(search_terms: str, count: int = 3) -> List[Dict[str, Any]]:
    """
    Search for images using Google Custom Search API (free tier: 100 queries/day).
    
    Args:
        search_terms: Search terms for images
        count: Number of images to return
        
    Returns:
        List of real product image dictionaries from Google
    """
    try:
        import requests
        
        # Check if API keys are configured
        google_api_key = app.config.get('GOOGLE_API_KEY')
        google_cx = app.config.get('GOOGLE_CUSTOM_SEARCH_ENGINE_ID')
        
        if not google_api_key or not google_cx:
            logger.info("Google Custom Search not configured (missing API key or CX ID)")
            return []
        
        # Google Custom Search API endpoint
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': google_api_key,
            'cx': google_cx,
            'q': f"{search_terms} product buy",
            'searchType': 'image',
            'num': min(count, 10),  # Max 10 per request
            'imgSize': 'medium',
            'imgType': 'photo',
            'safe': 'active',
            'fields': 'items(title,link,image)'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            images = []
            
            for item in data.get('items', []):
                if 'link' in item and 'image' in item:
                    # Filter out low-quality sources
                    image_url = item['link']
                    if not any(bad in image_url.lower() for bad in ['pinterest.com', 'blogspot.com']):
                        images.append({
                            'url': image_url,
                            'title': item.get('title', f'{search_terms} - Product {len(images) + 1}'),
                            'width': item['image'].get('width', 600),
                            'height': item['image'].get('height', 400),
                            'thumbnail': item['image'].get('thumbnailLink', image_url),
                            'source': 'Google Custom Search',
                            'photographer': 'Web Search Result'
                        })
                        
                        if len(images) >= count:
                            break
            
            logger.info(f"Google Custom Search found {len(images)} images for '{search_terms}'")
            return images
        else:
            logger.warning(f"Google Custom Search returned status {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Error in Google Custom Search: {str(e)}")
        return []

def get_improved_curated_images(search_terms: str, count: int = 3) -> List[Dict[str, Any]]:
    """
    Get improved curated images using real product photo URLs from multiple sources.
    
    Args:
        search_terms: Search terms for context
        count: Number of images to return
        
    Returns:
        List of improved curated image dictionaries with real product photos
    """
    # Extended database of real product images from reliable sources
    product_image_database = {
        'headphones': [
            # Sony headphones
            'https://images-na.ssl-images-amazon.com/images/I/61KYRD8B3KL._AC_SL1500_.jpg',
            'https://images-na.ssl-images-amazon.com/images/I/71pGIBjnpbL._AC_SL1500_.jpg',
            # Bose headphones
            'https://assets.bose.com/content/dam/Bose_DAM/Web/consumer_electronics/global/products/headphones/quietcomfort_earbuds/product_silo_images/qc_earbuds_black_EC_hero.jpg',
            # Apple AirPods
            'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/MQD83?wid=1144&hei=1144&fmt=jpeg&qlt=90&.v=1660803972361',
            # JBL headphones
            'https://in.jbl.com/dw/image/v2/BFND_PRD/on/demandware.static/-/Sites-masterCatalog_Harman/default/dw6f8c6c4f/JBL_LIVE_660NC_Product%20Image_Hero_White.png'
        ],
        'watch': [
            # Apple Watch
            'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/watch-s9-45mm-aluminum-midnight-nc-s9?wid=1000&hei=1000&fmt=p-jpg&qlt=95&.v=1692925775950',
            # Samsung Galaxy Watch
            'https://images.samsung.com/is/image/samsung/p6pim/in/2208/gallery/in-galaxy-watch5-r900-sm-r900nzsainu-532632081?$650_519_PNG$',
            # Fitbit
            'https://www.fitbit.com/global/content/dam/fitbit/global/products/devices/versa-4/hero/fitbit-versa-4-black-aluminum-black-sport-band-front-three-quarter.png',
            # Fossil watch
            'https://fossil.scene7.com/is/image/FossilPartners/FS5657_main?$sfcc_fos_large$',
            # Casio G-Shock
            'https://gshock.casio.com/content/casio/locales/intl/en/brands/gshock/products/timepieces/dw-5600e-1v/_jcr_content/root/responsivegrid/teaser_copy/image.casiocoreimg.jpeg/1659435669457/dw-5600e-1v-b1.jpeg'
        ],
        'coffee': [
            # Coffee beans
            'https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=800',
            'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=800',
            # Coffee machines
            'https://www.nespresso.com/ecom/medias/sys_master/public/27100848398366/C-D30-WH-W-coffee-machine-WEB.png',
            'https://images-na.ssl-images-amazon.com/images/I/81h-2jC5wKL._AC_SL1500_.jpg',
            # Coffee mugs
            'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=800'
        ],
        'book': [
            # Popular books
            'https://images-na.ssl-images-amazon.com/images/I/51Zymoq7UnL._SX325_BO1,204,203,200_.jpg',
            'https://images-na.ssl-images-amazon.com/images/I/41VSSVNyLYL._SX325_BO1,204,203,200_.jpg',
            'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800',
            'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=800',
            'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=800'
        ],
        'wallet': [
            # Leather wallets
            'https://images-na.ssl-images-amazon.com/images/I/81hCsEuFQaL._AC_UL1500_.jpg',
            'https://images-na.ssl-images-amazon.com/images/I/71XhOUE4k2L._AC_UL1500_.jpg',
            'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800',
            'https://images.unsplash.com/photo-1627123424574-724758594e93?w=800',
            'https://images.unsplash.com/photo-1609961354195-3a8ed83d9a13?w=800'
        ],
        'phone': [
            # iPhone
            'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-15-pro-finish-select-202309-6-7inch-bluetitanium?wid=1280&hei=492&fmt=p-jpg&qlt=80&.v=1692895706095',
            # Samsung Galaxy
            'https://images.samsung.com/is/image/samsung/p6pim/in/2202/gallery/in-galaxy-s22-s901-410318-sm-s901bzabins-530847445?$650_519_PNG$',
            # Google Pixel
            'https://lh3.googleusercontent.com/Nu3a6F80WfixUqf_ec_vgXy_c0-0r4VLJRXjjff6OEFvOHONQb8cALdw=w526-h296-l80-e365',
            'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=800'
        ]
    }
    
    # Find matching category
    search_lower = search_terms.lower()
    matched_urls = []
    
    for category, urls in product_image_database.items():
        if category in search_lower or any(word in search_lower for word in category.split()):
            matched_urls = urls
            break
    
    # If no specific match, use a general mix
    if not matched_urls:
        all_urls = []
        for urls in product_image_database.values():
            all_urls.extend(urls[:2])  # Take 2 from each category
        matched_urls = all_urls[:10]  # Limit to 10
    
    # Create image objects
    images = []
    for i, url in enumerate(matched_urls[:count]):
        images.append({
            'url': url,
            'title': f'{search_terms} - Premium Product {i + 1}',
            'width': 800,
            'height': 600,
            'thumbnail': url + '?w=300&h=200&fit=crop' if 'unsplash.com' in url else url,
            'source': 'Improved Curated Collection',
            'photographer': 'Professional Product Photography'
        })
    
    logger.info(f"Generated {len(images)} improved curated images for '{search_terms}'")
    return images

def get_curated_product_images(search_terms: str, count: int = 3) -> List[Dict[str, Any]]:
    """
    Get curated real product images from Unsplash using direct photo IDs.
    This bypasses the API and uses known good product photos with comprehensive keyword matching.
    """
    # Comprehensive map of search terms to specific Unsplash photo IDs for real products
    product_photo_mapping = {
        # Audio & Electronics
        'headphones': ['photo-1505740420928-5e560c06d30e', 'photo-1546435770-a3e426bf472b', 'photo-1583394838336-acd977736f90'],
        'earbuds': ['photo-1545127398-14699f92334b', 'photo-1484704849700-f032a568e944', 'photo-1572569511254-d8f925fe2cbb'],
        'speakers': ['photo-1608043152269-423dbba4e7e1', 'photo-1608043152269-642ea140fc76', 'photo-1593508512255-86ab42a8e620'],
        
        # Tech & Gadgets
        'laptop': ['photo-1496181133206-80ce9b88a853', 'photo-1515378791036-0648a814e3e8', 'photo-1498050108023-c5249f4df085'],
        'phone': ['photo-1511707171634-5f897ff02aa9', 'photo-1592750475338-74b7b21085ab', 'photo-1580910051074-3eb694886505'],
        'tablet': ['photo-1544244015-0df4b3ffc6b0', 'photo-1561154464-82e9adf32764', 'photo-1606813907291-d86efa9b94db'],
        
        # Fashion & Accessories
        'watch': ['photo-1523275335684-37898b6baf30', 'photo-1434493789847-2f02dc6ad3ba', 'photo-1524805444758-089113d48a6d'],
        'wallet': ['photo-1553062407-98eeb64c6a62', 'photo-1627123424574-724758594e93', 'photo-1609961354195-3a8ed83d9a13'],
        'bag': ['photo-1553062407-98eeb64c6a62', 'photo-1549298916-b41d501d3772', 'photo-1584917865442-de89df76afd3'],
        
        # Home & Lifestyle
        'coffee': ['photo-1495474472287-4d71bcdd2085', 'photo-1509042239860-f550ce710b93', 'photo-1447933601403-0c6688de566e'],
        'mug': ['photo-1501339847302-ac426a4a7cbb', 'photo-1544787219-7f47ccb76574', 'photo-1571091718767-18b5b1457add'],
        'tea': ['photo-1544787219-7f47ccb76574', 'photo-1571091718767-18b5b1457add', 'photo-1558618666-fcd25c85cd64'],
        
        # Books & Reading
        'book': ['photo-1507003211169-0a1dd7228f2d', 'photo-1481627834876-b7833e8f5570', 'photo-1544716278-ca5e3f4abd8c'],
        'journal': ['photo-1517971129774-39b2c2334c58', 'photo-1544947950-fa07a98d237f', 'photo-1506905925346-21bda4d32df4'],
        'planner': ['photo-1517971129774-39b2c2334c58', 'photo-1544947950-fa07a98d237f', 'photo-1587614382346-4ec70e388b28'],
        'notebook': ['photo-1517971129774-39b2c2334c58', 'photo-1544947950-fa07a98d237f', 'photo-1587614382346-4ec70e388b28'],
        
        # Beauty & Wellness
        'perfume': ['photo-1541643600914-78b084683601', 'photo-1588405748880-12d1d2a59d75', 'photo-1515377905703-c4788e51af15'],
        'skincare': ['photo-1556228453-efd6c1ff04f6', 'photo-1570554886111-e80fcca6a029', 'photo-1612817288484-6f916006741a'],
        'makeup': ['photo-1596462502278-27bfdc403348', 'photo-1522335789203-aabd1fc54bc9', 'photo-1487236985954-4d4d7e8e53ea'],
        
        # Plants & Garden
        'plant': ['photo-1416879595882-3373a0480b5b', 'photo-1485955900006-10f4d324d411', 'photo-1463320726281-696a485928c7'],
        'succulent': ['photo-1485955900006-10f4d324d411', 'photo-1416879595882-3373a0480b5b', 'photo-1558618666-fcd25c85cd64'],
        'flowers': ['photo-1490750967868-88aa4486c946', 'photo-1463320726281-696a485928c7', 'photo-1558618666-fcd25c85cd64'],
        
        # Candles & Aromatherapy
        'candle': ['photo-1602874801070-94c0af3e3759', 'photo-1572726729207-a78d6feb18d7', 'photo-1608571423902-eed4a5ad8108'],
        'aromatherapy': ['photo-1513475382585-d06e58bcb0e0', 'photo-1602874801070-94c0af3e3759', 'photo-1572726729207-a78d6feb18d7'],
        'essential oil': ['photo-1513475382585-d06e58bcb0e0', 'photo-1602874801070-94c0af3e3759', 'photo-1588405748880-12d1d2a59d75'],
        
        # Wellness & Health
        'meditation': ['photo-1506905925346-21bda4d32df4', 'photo-1571019613454-1cb2f99b2d8b', 'photo-1447452001602-7090c7ab2db3'],
        'yoga': ['photo-1544367567-0f2fcb009e0b', 'photo-1571019613454-1cb2f99b2d8b', 'photo-1506905925346-21bda4d32df4'],
        'fitness': ['photo-1571019613454-1cb2f99b2d8b', 'photo-1544367567-0f2fcb009e0b', 'photo-1434596922112-19c563067271'],
        
        # Art & Creativity
        'art': ['photo-1541961017774-22349e4a1262', 'photo-1578662996442-48f60103fc96', 'photo-1513475382585-d06e58bcb0e0'],
        'painting': ['photo-1541961017774-22349e4a1262', 'photo-1578662996442-48f60103fc96', 'photo-1506905925346-21bda4d32df4'],
        'craft': ['photo-1541961017774-22349e4a1262', 'photo-1578662996442-48f60103fc96', 'photo-1513475382585-d06e58bcb0e0'],
        
        # Kitchen & Cooking
        'kitchen': ['photo-1556724340-8e6ca2ed0ca9', 'photo-1556909114-f6e7ad7d3136', 'photo-1571019613454-1cb2f99b2d8b'],
        'cooking': ['photo-1556724340-8e6ca2ed0ca9', 'photo-1585238341710-4d3ee08618d9', 'photo-1571019613454-1cb2f99b2d8b'],
        'utensils': ['photo-1556724340-8e6ca2ed0ca9', 'photo-1585238341710-4d3ee08618d9', 'photo-1544947950-fa07a98d237f'],
        
        # Generic product categories with better variety
        'gift': ['photo-1549298916-b41d501d3772', 'photo-1513475382585-d06e58bcb0e0', 'photo-1544947950-fa07a98d237f'],
        'luxury': ['photo-1571019613454-1cb2f99b2d8b', 'photo-1588405748880-12d1d2a59d75', 'photo-1523275335684-37898b6baf30'],
        'eco friendly': ['photo-1416879595882-3373a0480b5b', 'photo-1485955900006-10f4d324d411', 'photo-1517971129774-39b2c2334c58']
    }
    
    # Advanced keyword matching - check for any keyword in search terms
    search_lower = search_terms.lower()
    matched_ids = []
    
    # First pass: exact category match
    for category, photo_ids in product_photo_mapping.items():
        if category in search_lower:
            matched_ids = photo_ids
            logger.info(f"Exact match found for category '{category}' in search terms '{search_terms}'")
            break
    
    # Second pass: partial keyword matching 
    if not matched_ids:
        for category, photo_ids in product_photo_mapping.items():
            category_words = category.split()
            search_words = search_lower.split()
            
            # Check if any category word appears in search terms
            if any(cat_word in search_lower for cat_word in category_words):
                matched_ids = photo_ids
                logger.info(f"Partial match found for category '{category}' in search terms '{search_terms}'")
                break
            
            # Check if any search word appears in category  
            if any(search_word in category for search_word in search_words):
                matched_ids = photo_ids
                logger.info(f"Reverse partial match found for category '{category}' in search terms '{search_terms}'")
                break
    
    # Third pass: fuzzy matching for common variations
    if not matched_ids:
        # Map common variations and synonyms
        variations = {
            'zen': 'meditation', 'mindfulness': 'meditation', 'relaxation': 'meditation',
            'indoor': 'plant', 'outdoor': 'plant', 'garden': 'plant', 'succulent': 'plant',
            'organizer': 'planner', 'diary': 'journal', 'schedule': 'planner',
            'wireless': 'headphones', 'bluetooth': 'headphones', 'audio': 'headphones',
            'fragrance': 'perfume', 'cologne': 'perfume', 'scent': 'perfume',
            'personalized': 'gift', 'custom': 'gift', 'handmade': 'craft'
        }
        
        for variation, category in variations.items():
            if variation in search_lower and category in product_photo_mapping:
                matched_ids = product_photo_mapping[category]
                logger.info(f"Fuzzy match found: '{variation}' -> '{category}' for search terms '{search_terms}'")
                break
    
    # Final fallback: use diverse general product photos (NOT the same 3 meditation images)
    if not matched_ids:
        logger.warning(f"No match found for search terms '{search_terms}', using diverse fallback images")
        matched_ids = [
            'photo-1549298916-b41d501d3772',  # Shopping bag
            'photo-1472851294608-062f824d29cc',  # Technology gadget
            'photo-1526170375885-4d8ecf77b99f',  # Lifestyle product
            'photo-1585238341710-4d3ee08618d9',  # Kitchen item
            'photo-1544947950-fa07a98d237f',   # Stationery
            'photo-1571019613454-1cb2f99b2d8b'   # Wellness product
        ]
    
    # Generate image URLs from photo IDs
    images = []
    for i, photo_id in enumerate(matched_ids[:count]):
        images.append({
            'url': f'https://images.unsplash.com/{photo_id}?w=600&h=400&fit=crop&crop=center',
            'title': f'{search_terms} - Product {i + 1}',
            'width': 600,
            'height': 400,
            'thumbnail': f'https://images.unsplash.com/{photo_id}?w=300&h=200&fit=crop&crop=center',
            'source': 'Curated Product Collection',
            'photographer': 'Unsplash Contributor',
            'photographer_url': f'https://unsplash.com/photos/{photo_id.replace("photo-", "")}'
        })
    
    logger.info(f"Generated {len(images)} curated product images for '{search_terms}'")
    return images

def search_jsonbin_products(search_terms: str, count: int = 3) -> List[Dict[str, Any]]:
    """Search for products in JSONBin free database."""
    return []  # Placeholder for now

def search_duckduckgo_images(search_terms: str, count: int = 3) -> List[Dict[str, Any]]:
    """
    Search for real product images using DuckDuckGo image search with multiple robust methods.
    Implements various approaches including library-based search and direct scraping.
    
    Args:
        search_terms: Search terms for images
        count: Number of images to return
        
    Returns:
        List of real product image dictionaries from DuckDuckGo
    """
    try:
        # Method 1: Try using duckduckgo-search library if available
        try:
            logger.info(f"Attempting DuckDuckGo library search for: '{search_terms}'")
            images = _search_with_ddg_library(search_terms, count)
            if images:
                logger.info(f"✓ Found {len(images)} images using DDG library")
                return images
        except ImportError:
            logger.info("duckduckgo-search library not available, trying manual methods")
        except Exception as e:
            logger.warning(f"DDG library search failed: {str(e)}")
        
        # Method 2: Enhanced manual search with better product targeting
        try:
            logger.info(f"Attempting enhanced manual DDG search for: '{search_terms}'")
            images = _search_ddg_manual_enhanced(search_terms, count)
            if images:
                logger.info(f"✓ Found {len(images)} images using enhanced manual search")
                return images
        except Exception as e:
            logger.warning(f"Enhanced manual search failed: {str(e)}")
        
        # Method 3: Simplified web scraping approach
        try:
            logger.info(f"Attempting simplified web scraping for: '{search_terms}'")
            images = _search_ddg_web_scraping(search_terms, count)
            if images:
                logger.info(f"✓ Found {len(images)} images using web scraping")
                return images
        except Exception as e:
            logger.warning(f"Web scraping search failed: {str(e)}")
        
        logger.warning(f"All DuckDuckGo methods failed for '{search_terms}'")
        return []
            
    except Exception as e:
        logger.error(f"Critical error in DuckDuckGo search: {str(e)}")
        return []

def _search_with_ddg_library(search_terms: str, count: int) -> List[Dict[str, Any]]:
    """Try using the duckduckgo-search library for more reliable results."""
    try:
        from duckduckgo_search import DDGS
        
        # Create specific product search query
        product_query = f"{search_terms} product buy shopping"
        
        images = []
        with DDGS() as ddgs:
            ddg_images = ddgs.images(
                keywords=product_query,
                region="us-en",
                safesearch="moderate",
                size="medium",
                max_results=count * 2  # Get extra to filter
            )
            
            for i, img in enumerate(ddg_images[:count]):
                if img.get('image') and img.get('thumbnail'):
                    # Basic quality filtering
                    image_url = img['image']
                    if not any(bad in image_url.lower() for bad in ['pinterest.com', 'blogspot.com']):
                        images.append({
                            'url': image_url,
                            'title': img.get('title', f'{search_terms} - Product {i + 1}'),
                            'width': img.get('width', 600),
                            'height': img.get('height', 400),
                            'thumbnail': img.get('thumbnail', image_url),
                            'source': 'DuckDuckGo Library',
                            'source_url': img.get('url', ''),
                            'photographer': 'Web Search Result'
                        })
                        
                        if len(images) >= count:
                            break
        
        return images
        
    except ImportError:
        # Library not installed
        raise ImportError("duckduckgo-search library not available")
    except Exception as e:
        logger.error(f"DDG library error: {str(e)}")
        return []

def _search_ddg_manual_enhanced(search_terms: str, count: int) -> List[Dict[str, Any]]:
    """Enhanced manual search with better targeting and retry logic."""
    import requests
    import re
    import time
    import random
    from urllib.parse import quote_plus
    
    # Create multiple search variations for better results
    search_variations = [
        f"{search_terms} product",
        f"{search_terms} buy online",
        f"{search_terms} shop",
        f"buy {search_terms}",
        search_terms  # Original as fallback
    ]
    
    for variation in search_variations:
        try:
            logger.info(f"Trying search variation: '{variation}'")
            
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'DNT': '1'
            })
            
            # Use DuckDuckGo instant answers API approach
            search_url = "https://api.duckduckgo.com/"
            params = {
                'q': variation,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = session.get(search_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Look for image data in the response
                if 'Image' in data and data['Image']:
                    images = []
                    images.append({
                        'url': data['Image'],
                        'title': data.get('Heading', f'{search_terms} - Product 1'),
                        'width': 600,
                        'height': 400,
                        'thumbnail': data['Image'],
                        'source': 'DuckDuckGo API',
                        'source_url': data.get('FirstURL', ''),
                        'photographer': 'Web Search Result'
                    })
                    return images
            
            # Small delay between attempts
            time.sleep(random.uniform(0.5, 1.0))
            
        except Exception as e:
            logger.debug(f"Search variation '{variation}' failed: {str(e)}")
            continue
    
    return []

def _search_ddg_web_scraping(search_terms: str, count: int) -> List[Dict[str, Any]]:
    """Simplified web scraping approach targeting specific e-commerce sites."""
    import requests
    import re
    from urllib.parse import quote_plus
    
    # Target e-commerce sites that are likely to have product images
    ecommerce_sites = [
        f"site:amazon.com {search_terms}",
        f"site:ebay.com {search_terms}",
        f"site:etsy.com {search_terms}",
        f"site:alibaba.com {search_terms}",
        f"site:shopify.com {search_terms}"
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    })
    
    images = []
    
    for site_query in ecommerce_sites:
        try:
            # Use DuckDuckGo HTML search
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(site_query)}"
            
            response = session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                # Look for image URLs in the HTML response
                image_patterns = [
                    r'data-src="([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
                    r'src="([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
                    r'url\(["\']([^"\']+\.(?:jpg|jpeg|png|webp)[^"\']*)["\']?\)',
                ]
                
                found_urls = set()
                
                for pattern in image_patterns:
                    matches = re.findall(pattern, response.text, re.IGNORECASE)
                    for match in matches:
                        clean_url = match.replace('\\/', '/').strip()
                        if (clean_url.startswith('http') and 
                            len(clean_url) > 30 and 
                            not any(bad in clean_url.lower() for bad in ['icon', 'logo', 'avatar', 'thumb'])):
                            found_urls.add(clean_url)
                
                # Convert found URLs to our format
                for i, url in enumerate(list(found_urls)[:count - len(images)]):
                    images.append({
                        'url': url,
                        'title': f'{search_terms} - Product {len(images) + 1}',
                        'width': 600,
                        'height': 400,
                        'thumbnail': url,
                        'source': 'DuckDuckGo Scraping',
                        'photographer': 'Web Search Result'
                    })
                    
                    if len(images) >= count:
                        break
                
                if len(images) >= count:
                    break
                    
        except Exception as e:
            logger.debug(f"Site query '{site_query}' failed: {str(e)}")
            continue
    
    return images

def _extract_vqd_token_traditional(session: requests.Session, search_terms: str) -> str:
    """Extract vqd token using traditional method."""
    import re
    from urllib.parse import quote_plus
    
    search_query = quote_plus(search_terms)
    search_url = f"https://duckduckgo.com/?q={search_query}&iar=images&iax=images&ia=images"
    
    response = session.get(search_url, timeout=15)
    
    if response.status_code != 200:
        return None
    
    # Enhanced vqd token patterns - more comprehensive search
    vqd_patterns = [
        r'vqd["\']?\s*[=:]\s*["\']([^"\']+)["\']',
        r'vqd["\']\s*:\s*["\']([^"\']+)["\']',
        r'"vqd"\s*:\s*"([^"]+)"',
        r"'vqd'\s*:\s*'([^']+)'",
        r'vqd=([a-zA-Z0-9\-_]+)',
        r'&vqd=([a-zA-Z0-9\-_]+)',
        r'data-vqd["\']?\s*=\s*["\']([^"\']+)["\']',
        r'vqd["\']\s*,\s*["\']([^"\']+)["\']'
    ]
    
    for pattern in vqd_patterns:
        matches = re.findall(pattern, response.text, re.IGNORECASE)
        if matches:
            # Return the first valid-looking token
            for match in matches:
                if len(match) > 10 and '-' in match:  # vqd tokens typically have dashes and are long
                    return match
    
    return None

def _fetch_images_with_vqd(session: requests.Session, search_terms: str, vqd_token: str, count: int, original_terms: str) -> List[Dict[str, Any]]:
    """Fetch images using vqd token."""
    api_url = "https://duckduckgo.com/i.js"
    params = {
        'l': 'us-en',
        'o': 'json',
        'q': search_terms,
        'vqd': vqd_token,
        'f': ',,,,,1,',
        'p': '1',
        's': '0',
        'u': 'bing'
    }
    
    # Add delay to avoid rate limiting
    time.sleep(random.uniform(0.5, 1.5))
    
    response = session.get(api_url, params=params, timeout=15)
    
    if response.status_code == 200:
        try:
            data = response.json()
            return _process_ddg_results(data, count, original_terms)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse vqd response: {str(e)}")
    
    return []

def _fetch_images_alternative_api(session: requests.Session, search_terms: str, count: int, original_terms: str) -> List[Dict[str, Any]]:
    """Try alternative DuckDuckGo API endpoints."""
    import time
    import json
    from urllib.parse import quote_plus
    
    # Try the newer API endpoint
    try:
        search_url = "https://duckduckgo.com/i.js"
        params = {
            'q': search_terms,
            'o': 'json',
            'p': '1',
            's': '0',
            'u': 'bing',
            'f': ',,,,,1,'
        }
        
        # First get a basic page to establish session
        base_url = f"https://duckduckgo.com/?q={quote_plus(search_terms)}&iar=images"
        session.get(base_url, timeout=10)
        
        time.sleep(1)
        
        response = session.get(search_url, params=params, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                return _process_ddg_results(data, count, original_terms)
            except json.JSONDecodeError:
                pass
    except:
        pass
    
    return []

def _fetch_images_html_parsing(session: requests.Session, search_terms: str, count: int, original_terms: str) -> List[Dict[str, Any]]:
    """Parse HTML directly for image results."""
    import re
    from urllib.parse import quote_plus
    
    search_url = f"https://duckduckgo.com/?q={quote_plus(search_terms)}&iar=images&iax=images&ia=images"
    
    response = session.get(search_url, timeout=15)
    
    if response.status_code != 200:
        return []
    
    # Look for image URLs in the HTML
    image_patterns = [
        r'"image":"([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
        r'"thumbnail":"([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
        r'data-src="([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
        r'src="([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"'
    ]
    
    found_images = set()
    
    for pattern in image_patterns:
        urls = re.findall(pattern, response.text, re.IGNORECASE)
        for url in urls:
            # Clean and validate URL
            clean_url = url.replace('\\/', '/').replace('\\', '')
            if clean_url.startswith('http') and len(clean_url) > 20:
                found_images.add(clean_url)
    
    # Convert to our format
    images = []
    for i, url in enumerate(list(found_images)[:count]):
        images.append({
            'url': url,
            'title': f"{original_terms} - Product {i + 1}",
            'width': 600,
            'height': 400,
            'thumbnail': url,  # Use same URL for thumbnail
            'source': 'DuckDuckGo HTML',
            'photographer': 'Web Search Result'
        })
    
    return images

def _process_ddg_results(data: dict, count: int, original_terms: str) -> List[Dict[str, Any]]:
    """Process DuckDuckGo API results into our format."""
    images = []
    results = data.get('results', [])
    
    logger.info(f"Processing {len(results)} DuckDuckGo results")
    
    for i, result in enumerate(results[:count * 2]):  # Get extra to filter
        try:
            if 'image' in result:
                image_url = result['image']
                thumbnail_url = result.get('thumbnail', image_url)
                title = result.get('title', f"{original_terms} - Product {i + 1}")
                source_url = result.get('url', '')
                
                # Quality filters - exclude low-quality sources
                bad_domains = ['pinterest.com', 'blogspot.com', 'tumblr.com', 'reddit.com']
                good_extensions = ['.jpg', '.jpeg', '.png', '.webp']
                
                if (image_url and thumbnail_url and
                    not any(bad in image_url.lower() for bad in bad_domains) and
                    any(ext in image_url.lower() for ext in good_extensions) and
                    len(image_url) > 20):
                    
                    images.append({
                        'url': image_url,
                        'title': title,
                        'width': result.get('width', 600),
                        'height': result.get('height', 400),
                        'thumbnail': thumbnail_url,
                        'source': 'DuckDuckGo Images',
                        'source_url': source_url,
                        'photographer': 'Web Search Result'
                    })
                    
                    if len(images) >= count:
                        break
        except Exception as e:
            logger.debug(f"Error processing result {i}: {str(e)}")
            continue
    
    logger.info(f"Successfully processed {len(images)} DuckDuckGo images")
    return images

def search_bing_images_enhanced(search_terms: str, count: int = 3) -> List[Dict[str, Any]]:
    """
    Enhanced Bing image search with better product targeting and multiple strategies.
    
    Args:
        search_terms: Search terms for images
        count: Number of images to return
        
    Returns:
        List of real product image dictionaries from Bing
    """
    try:
        import requests
        from urllib.parse import quote_plus
        import re
        import json
        import time
        import random
        
        # Create product-focused search variations
        search_variations = [
            f"{search_terms} product buy",
            f"{search_terms} shopping online",
            f"buy {search_terms} online",
            f"{search_terms} store",
            search_terms  # Original as fallback
        ]
        
        images = []
        
        for variation in search_variations:
            if len(images) >= count:
                break
                
            try:
                logger.info(f"Trying Bing search variation: '{variation}'")
                
                # Enhanced search query with product focus
                search_query = quote_plus(f"{variation} -pinterest -tumblr")
                search_url = f"https://www.bing.com/images/search?q={search_query}&FORM=HDRSC2&first=1&count=35"
                
                headers = {
                    'User-Agent': random.choice([
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0'
                    ]),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'DNT': '1'
                }
                
                response = requests.get(search_url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    # Enhanced pattern matching for better image extraction
                    image_patterns = [
                        r'"murl":"([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
                        r'"imgurl":"([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
                        r'"turl":"([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
                        r'data-src="([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
                        r'src="([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
                        r'mediaurl&quot;:&quot;([^&]+\.(?:jpg|jpeg|png|webp)[^&]*)',
                        r'"mediaUrl":"([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"'
                    ]
                    
                    thumbnail_patterns = [
                        r'"turl":"([^"]+)"',
                        r'"thumburl":"([^"]+)"',
                        r'thumbnail["\']?\s*:\s*["\']([^"\']+)["\']'
                    ]
                    
                    found_images = set()
                    found_thumbnails = set()
                    
                    # Extract main image URLs
                    for pattern in image_patterns:
                        urls = re.findall(pattern, response.text)
                        for url in urls:
                            # Clean and decode URL
                            clean_url = url.replace('\\u002f', '/').replace('\\/', '/').replace('&amp;', '&')
                            if (clean_url.startswith('http') and 
                                len(clean_url) > 20 and
                                any(ext in clean_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']) and
                                not any(bad in clean_url.lower() for bad in ['favicon', 'icon', 'logo', 'avatar', 'pinterest.com', 'blogspot.com'])):
                                found_images.add(clean_url)
                    
                    # Extract thumbnails
                    for pattern in thumbnail_patterns:
                        urls = re.findall(pattern, response.text)
                        for url in urls:
                            clean_url = url.replace('\\u002f', '/').replace('\\/', '/').replace('&amp;', '&')
                            if clean_url.startswith('http'):
                                found_thumbnails.add(clean_url)
                    
                    # Create image objects with quality filtering
                    thumbnail_list = list(found_thumbnails)
                    for i, image_url in enumerate(list(found_images)[:count * 2]):  # Get extras to filter
                        # Quality check - prefer images from known good domains
                        good_domains = ['amazon.com', 'ebay.com', 'aliexpress.com', 'shopify.com', 'etsy.com', 'walmart.com', 'target.com']
                        is_good_domain = any(domain in image_url.lower() for domain in good_domains)
                        
                        # Basic size check (avoid tiny images)
                        if len(image_url) > 40 or is_good_domain:
                            thumbnail = thumbnail_list[i] if i < len(thumbnail_list) else image_url
                            
                            images.append({
                                'url': image_url,
                                'title': f"{search_terms} - Product {len(images) + 1}",
                                'width': 600,
                                'height': 400,
                                'thumbnail': thumbnail,
                                'source': 'Bing Images Enhanced',
                                'photographer': 'Web Search Result',
                                'quality_score': 2 if is_good_domain else 1
                            })
                            
                            if len(images) >= count:
                                break
                
                # Add delay between search variations
                time.sleep(random.uniform(0.5, 1.5))
                
            except Exception as e:
                logger.debug(f"Bing search variation '{variation}' failed: {str(e)}")
                continue
        
        # Sort by quality score (good domains first)
        images.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        if images:
            logger.info(f"Enhanced Bing search found {len(images)} real product images for '{search_terms}'")
            
        return images[:count]
        
    except Exception as e:
        logger.error(f"Error in enhanced Bing search: {str(e)}")
        return []

def search_bing_images(search_terms: str, count: int = 3) -> List[Dict[str, Any]]:
    """
    Search for real product images using Bing image search (no API key required).
    
    Args:
        search_terms: Search terms for images
        count: Number of images to return
        
    Returns:
        List of real product image dictionaries from Bing
    """
    try:
        import requests
        from urllib.parse import quote_plus
        import re
        import json
        
        # Bing image search URL with more specific product search
        search_query = quote_plus(f"{search_terms} product buy shopping")
        search_url = f"https://www.bing.com/images/search?q={search_query}&FORM=HDRSC2&first=1"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(search_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # Multiple patterns to extract image data
            patterns = [
                r'"murl":"([^"]+)"',
                r'"imgurl":"([^"]+)"',
                r'data-src="([^"]*\.(?:jpg|jpeg|png|webp)[^"]*)"',
                r'src="([^"]*\.(?:jpg|jpeg|png|webp)[^"]*)"'
            ]
            
            thumbnail_patterns = [
                r'"turl":"([^"]+)"',
                r'"thumburl":"([^"]+)"'
            ]
            
            image_urls = []
            thumbnail_urls = []
            
            # Try each pattern
            for pattern in patterns:
                urls = re.findall(pattern, response.text)
                if urls:
                    # Clean and decode URLs
                    for url in urls:
                        clean_url = url.replace('\\u002f', '/').replace('\\//', '//')
                        if clean_url.startswith('http') and any(ext in clean_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                            image_urls.append(clean_url)
                    if len(image_urls) >= count:
                        break
            
            # Get thumbnails
            for pattern in thumbnail_patterns:
                thumb_urls = re.findall(pattern, response.text)
                if thumb_urls:
                    for url in thumb_urls:
                        clean_url = url.replace('\\u002f', '/').replace('\\//', '//')
                        if clean_url.startswith('http'):
                            thumbnail_urls.append(clean_url)
                    if len(thumbnail_urls) >= count:
                        break
            
            # Create image objects
            images = []
            for i in range(min(count, len(image_urls))):
                thumbnail = thumbnail_urls[i] if i < len(thumbnail_urls) else image_urls[i]
                
                images.append({
                    'url': image_urls[i],
                    'title': f"{search_terms} - Product {i + 1}",
                    'width': 600,
                    'height': 400,
                    'thumbnail': thumbnail,
                    'source': 'Bing Images',
                    'photographer': 'Web Search Result'
                })
            
            if images:
                logger.info(f"Found {len(images)} real product images from Bing for '{search_terms}'")
                return images
            else:
                logger.warning(f"No valid image URLs extracted from Bing for '{search_terms}'")
                
        logger.warning(f"Bing search returned status {response.status_code} for '{search_terms}'")
        return []
        
    except Exception as e:
        logger.error(f"Error searching Bing images: {str(e)}")
        return []

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
    Search for real product images prioritizing DuckDuckGo image search.
    Falls back through multiple services: DuckDuckGo -> Bing -> Pixabay -> Placeholders.
    
    Args:
        search_terms: Keywords to search for images
        count: Number of images to return
        
    Returns:
        List of image dictionaries with url, title, etc.
    """
    try:
        # Clean the search terms for better product results
        cleaned_terms = clean_search_terms(search_terms)
        logger.info(f"Searching for real product images: '{search_terms}' (cleaned: '{cleaned_terms}')")
        
        images = []
        
        # PRIMARY: Try enhanced Bing image search for real products (most reliable)
        if len(images) < count:
            try:
                logger.info(f"Attempting enhanced Bing image search for '{cleaned_terms}'")
                bing_images = search_bing_images_enhanced(cleaned_terms, count - len(images))
                if bing_images:
                    images.extend(bing_images)
                    logger.info(f"✓ Added {len(bing_images)} real product images from Bing")
                else:
                    logger.warning("Enhanced Bing returned no images")
            except Exception as e:
                logger.warning(f"Enhanced Bing image search failed: {str(e)}")
        
        # SECONDARY: Try DuckDuckGo image search for real products
        if len(images) < count:
            try:
                logger.info(f"Attempting DuckDuckGo image search for '{cleaned_terms}'")
                duckduckgo_images = search_duckduckgo_images(cleaned_terms, count - len(images))
                if duckduckgo_images:
                    images.extend(duckduckgo_images)
                    logger.info(f"✓ Added {len(duckduckgo_images)} real product images from DuckDuckGo")
                else:
                    logger.warning("DuckDuckGo returned no images")
            except Exception as e:
                logger.warning(f"DuckDuckGo image search failed: {str(e)}")
        
        # TERTIARY: Try original Bing search as backup
        if len(images) < count:
            try:
                logger.info(f"Attempting original Bing image search for '{cleaned_terms}'")
                bing_images = search_bing_images(cleaned_terms, count - len(images))
                if bing_images:
                    images.extend(bing_images)
                    logger.info(f"✓ Added {len(bing_images)} real product images from Bing (backup)")
                else:
                    logger.warning("Original Bing returned no images")
            except Exception as e:
                logger.warning(f"Original Bing image search failed: {str(e)}")
        
        # TERTIARY: Try Pixabay for real product photos
        if len(images) < count:
            try:
                logger.info(f"Attempting Pixabay search for '{cleaned_terms}'")
                pixabay_images = generate_pixabay_images(cleaned_terms, count - len(images))
                if pixabay_images:
                    images.extend(pixabay_images)
                    logger.info(f"✓ Added {len(pixabay_images)} product images from Pixabay")
                else:
                    logger.warning("Pixabay returned no images")
            except Exception as e:
                logger.warning(f"Pixabay search failed: {str(e)}")
        
        # FALLBACK 1: Try Google Custom Search if configured
        if len(images) < count:
            try:
                logger.info(f"Attempting Google Custom Search for '{cleaned_terms}'")
                google_images = search_google_custom_images(cleaned_terms, count - len(images))
                if google_images:
                    images.extend(google_images)
                    logger.info(f"✓ Added {len(google_images)} real product images from Google")
                else:
                    logger.warning("Google Custom Search returned no images")
            except Exception as e:
                logger.warning(f"Google Custom Search failed: {str(e)}")
        
        # FALLBACK 2: Use improved curated product images with real URLs
        if len(images) < count:
            try:
                logger.info(f"Using improved curated product images for '{cleaned_terms}'")
                curated_images = get_improved_curated_images(cleaned_terms, count - len(images))
                if curated_images:
                    images.extend(curated_images)
                    logger.info(f"Added {len(curated_images)} improved curated images")
            except Exception as e:
                logger.warning(f"Improved curated images failed: {str(e)}")
        
        # FALLBACK 3: Traditional curated images as last resort
        if len(images) < count:
            try:
                logger.info(f"Using traditional curated images as final fallback for '{cleaned_terms}'")
                curated_images = get_curated_product_images(cleaned_terms, count - len(images))
                if curated_images:
                    images.extend(curated_images)
                    logger.info(f"Added {len(curated_images)} traditional curated images")
            except Exception as e:
                logger.warning(f"Traditional curated images failed: {str(e)}")
        
        # FINAL FALLBACK: Enhanced placeholder images
        if len(images) < count and app.config.get('USE_PLACEHOLDER_FALLBACK', True):
            remaining = count - len(images)
            placeholder_images = generate_enhanced_placeholder_images(search_terms, remaining)
            images.extend(placeholder_images)
            logger.info(f"Added {len(placeholder_images)} placeholder images as final fallback")
        
        # Log final results
        source_breakdown = {}
        for img in images:
            source = img.get('source', 'Unknown')
            source_breakdown[source] = source_breakdown.get(source, 0) + 1
        
        logger.info(f"✓ Successfully found {len(images)} total images for '{search_terms}' | Sources: {source_breakdown}")
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

@app.route('/questionnaire')
def serve_questionnaire():
    """Serve questionnaire page - same as main page but different URL."""
    return serve_frontend()

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
        
        # Log the received data for debugging
        logger.info(f"Received request data: {list(data.keys()) if data else 'None'}")
        
        # Validate input data
        is_valid, error_message = validate_questionnaire_data(data)
        if not is_valid:
            logger.warning(f"Invalid input data: {error_message}")
            logger.warning(f"Received data: {data}")
            return jsonify({
                "success": False,
                "error": error_message,
                "code": "INVALID_INPUT",
                "received_fields": list(data.keys()) if data else [],
                "required_fields": REQUIRED_QUESTIONS,
                "debug_info": f"Environment: {Config.FLASK_ENV}"
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
        
        # Store results with unique ID for URL routing
        result_id = store_result(data, gift_data['gift_ideas'])
        
        return jsonify({
            "success": True,
            "gift_ideas": gift_data['gift_ideas'],
            "result_id": result_id,
            "result_url": f"/results/{result_id}",
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in generate_gifts endpoint: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        
        # Provide more specific error messages for debugging
        error_message = "Internal server error occurred while generating gift ideas"
        error_code = "INTERNAL_ERROR"
        
        # Check if it's an OpenAI-related error
        if "OpenAI" in str(e) or "AI service" in str(e):
            error_message = str(e)
            error_code = "AI_SERVICE_ERROR"
        elif "timeout" in str(e).lower():
            error_message = "Request timed out while generating gift ideas. Please try again."
            error_code = "TIMEOUT_ERROR"
        elif "connection" in str(e).lower():
            error_message = "Failed to connect to AI service. Please try again."
            error_code = "CONNECTION_ERROR"
        
        return jsonify({
            "success": False,
            "error": error_message,
            "code": error_code,
            "debug_info": {
                "environment": Config.FLASK_ENV,
                "error_type": type(e).__name__,
                "openai_configured": bool(app.config.get('OPENAI_API_KEY'))
            }
        }), 500

@app.route('/results/<result_id>')
def view_results(result_id: str):
    """
    Serve results page with specific result ID.
    This allows for bookmarkable/shareable result URLs.
    """
    try:
        # Get results from storage
        result_data = get_result(result_id)
        
        if not result_data:
            # Result not found or expired
            logger.warning(f"Result not found or expired: {result_id}")
            return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Results Not Found - Ruby's Gifts</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        .error { color: #ff6600; margin: 20px 0; }
        .btn { background: #ff6600; color: white; padding: 10px 20px; 
               text-decoration: none; border-radius: 20px; }
    </style>
</head>
<body>
    <h1>Results Not Found</h1>
    <p class="error">The results you're looking for have expired or don't exist.</p>
    <a href="/" class="btn">Start New Search</a>
</body>
</html>
            """), 404
        
        # Load the main HTML with the result_id in URL
        with open('index.html', 'r') as f:
            html_content = f.read()
        
        # Inject result data into the page for JavaScript to use
        # Convert datetime objects to ISO strings for JSON serialization
        serializable_data = {
            'id': result_data['id'],
            'gift_ideas': result_data['gift_ideas'],
            'questions_answers': result_data['questions_answers'],
            'created_at': result_data['created_at'].isoformat(),
            'expires_at': result_data['expires_at'].isoformat()
        }
        
        script_injection = f"""
    <script>
        window.RESULT_DATA = {json.dumps(serializable_data)};
        window.RESULT_ID = "{result_id}";
    </script>
        """
        
        # Insert before closing head tag
        html_content = html_content.replace('</head>', f'{script_injection}</head>')
        
        return html_content
        
    except Exception as e:
        logger.error(f"Error serving results page for {result_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Error loading results page",
            "code": "RESULTS_PAGE_ERROR"
        }), 500

@app.route('/api/results/<result_id>')
def get_results_api(result_id: str):
    """
    API endpoint to get results data by ID.
    Used by JavaScript to load results dynamically.
    """
    try:
        result_data = get_result(result_id)
        
        if not result_data:
            return jsonify({
                "success": False,
                "error": "Results not found or expired",
                "code": "RESULTS_NOT_FOUND"
            }), 404
        
        return jsonify({
            "success": True,
            "result_id": result_id,
            "gift_ideas": result_data['gift_ideas'],
            "questions_answers": result_data['questions_answers'],
            "created_at": result_data['created_at'].isoformat(),
            "expires_at": result_data['expires_at'].isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error retrieving results {result_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Error retrieving results",
            "code": "RESULTS_RETRIEVAL_ERROR"
        }), 500

@app.route('/cleanup', methods=['POST'])
def manual_cleanup():
    """Manual cleanup endpoint for expired results (admin use)."""
    try:
        cleanup_expired_results()
        return jsonify({
            "success": True,
            "message": "Cleanup completed successfully"
        })
    except Exception as e:
        logger.error(f"Error during manual cleanup: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Cleanup failed",
            "code": "CLEANUP_ERROR"
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