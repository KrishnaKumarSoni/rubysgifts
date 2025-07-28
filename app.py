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
from datetime import datetime
from typing import Dict, List, Any, Optional

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

Format as JSON:
{{
  "gift_ideas": [
    {{
      "title": "Creative, specific gift name",
      "description": "Detailed explanation with psychological reasoning combining why this fits their personality/needs",
      "starter": "Exactly how to introduce/present this gift",
      "reaction": "Realistic emotional response based on their personality"
    }},
    {{
      "title": "Creative, specific gift name", 
      "description": "Detailed explanation with psychological reasoning combining why this fits their personality/needs",
      "starter": "Exactly how to introduce/present this gift", 
      "reaction": "Realistic emotional response based on their personality"
    }},
    {{
      "title": "Creative, specific gift name",
      "description": "Detailed explanation with psychological reasoning combining why this fits their personality/needs",
      "starter": "Exactly how to introduce/present this gift",
      "reaction": "Realistic emotional response based on their personality"
    }}
  ]
}}

Ensure all recommendations are within budget, respect limitations, and demonstrate the thoughtfulness that strengthens relationships."""

    return prompt

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
                    "content": "You are a world-class gift psychology expert. Apply step-by-step analytical thinking and respond with valid JSON containing exactly 3 gift ideas in this format: {\"gift_ideas\": [{\"title\": \"Creative gift name\", \"description\": \"Detailed psychological reasoning\", \"starter\": \"Presentation strategy\", \"reaction\": \"Authentic emotional response\"}]}"
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

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Ruby's Gifts API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "openai_configured": bool(app.config.get('OPENAI_API_KEY')),
        "api_key_present": bool(app.config.get('OPENAI_API_KEY'))
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
                "reaction": "Expected reaction"
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
        
        # Validate each gift idea has required fields
        required_fields = ['title', 'description', 'starter', 'reaction']
        for i, gift in enumerate(gift_data['gift_ideas']):
            for field in required_fields:
                if field not in gift or not gift[field]:
                    logger.error(f"Gift idea {i+1} missing required field: {field}")
                    return jsonify({
                        "success": False,
                        "error": "Incomplete gift idea generated",
                        "code": "INCOMPLETE_AI_RESPONSE"
                    }), 500
        
        logger.info(f"Successfully generated {len(gift_data['gift_ideas'])} gift ideas")
        
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