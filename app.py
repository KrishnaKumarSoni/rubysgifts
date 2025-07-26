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
import openai
from openai import OpenAI

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
    
    # OpenAI Configuration
    OPENAI_MODEL = 'gpt-4o-mini'
    OPENAI_MAX_TOKENS = 1500
    OPENAI_TEMPERATURE = 0.7

app.config.from_object(Config)

# Enable CORS for all routes
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5000"])

# Initialize OpenAI client
if not app.config['OPENAI_API_KEY']:
    logger.error("OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY is required")

openai_client = OpenAI(api_key=app.config['OPENAI_API_KEY'])

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
    Create a comprehensive prompt for OpenAI to generate personalized gift ideas.
    
    Args:
        answers: Dictionary containing sanitized questionnaire responses
        
    Returns:
        Formatted prompt string
    """
    prompt = f"""You are a creative gift advisor helping someone find the perfect personalized gifts. 

Based on the following information about the gift recipient, generate 3 unique and thoughtful gift ideas:

RECIPIENT DETAILS:
- What they call them: {answers['call_them']}
- Relationship: {answers['relationship']}
- Previous gifts given: {answers['previous_gifts']}
- Things they hate: {answers['hate']}
- What they complain about: {answers['complaints']}
- Their quirks/habits: {answers['complain_about_them']}
- Budget: {answers['budget']}
- Limitations/constraints: {answers['limitations']}

For each gift idea, provide:
1. A creative gift name/title
2. A detailed description explaining why this gift would be perfect
3. A conversation starter about how to present or discuss this gift
4. A predicted positive reaction the recipient might have

Make the suggestions:
- Highly personalized based on the provided information
- Creative and thoughtful, not generic
- Respectful of the budget and limitations
- Considerate of what they hate and complain about
- Appropriate for the relationship type

Format your response as a JSON object with this exact structure:
{{
  "gift_ideas": [
    {{
      "title": "Gift Name",
      "description": "Detailed explanation of the gift and why it's perfect",
      "starter": "How to present or discuss this gift",
      "reaction": "Predicted positive reaction"
    }},
    {{
      "title": "Gift Name",
      "description": "Detailed explanation of the gift and why it's perfect", 
      "starter": "How to present or discuss this gift",
      "reaction": "Predicted positive reaction"  
    }},
    {{
      "title": "Gift Name",
      "description": "Detailed explanation of the gift and why it's perfect",
      "starter": "How to present or discuss this gift", 
      "reaction": "Predicted positive reaction"
    }}
  ]
}}

Ensure the JSON is valid and properly formatted."""

    return prompt

def generate_gift_ideas(answers: Dict[str, str]) -> Dict[str, Any]:
    """
    Generate gift ideas using OpenAI API.
    
    Args:
        answers: Dictionary containing sanitized questionnaire responses
        
    Returns:
        Dictionary containing generated gift ideas or error information
        
    Raises:
        Exception: If OpenAI API call fails
    """
    try:
        prompt = create_gift_generation_prompt(answers)
        
        logger.info("Sending request to OpenAI API")
        
        response = openai_client.chat.completions.create(
            model=app.config['OPENAI_MODEL'],
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful and creative gift advisor. Always respond with valid JSON only."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=app.config['OPENAI_MAX_TOKENS'],
            temperature=app.config['OPENAI_TEMPERATURE'],
            response_format={"type": "json_object"}
        )
        
        # Extract and parse the response
        content = response.choices[0].message.content
        logger.info(f"Received response from OpenAI: {len(content)} characters")
        
        import json
        try:
            gift_data = json.loads(content)
            return gift_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            logger.error(f"Raw response: {content}")
            raise Exception("Invalid JSON response from AI service")
            
    except openai.APITimeoutError:
        logger.error("OpenAI API request timed out")
        raise Exception("AI service request timed out. Please try again.")
    
    except openai.RateLimitError:
        logger.error("OpenAI API rate limit exceeded")
        raise Exception("AI service rate limit exceeded. Please try again later.")
    
    except openai.APIConnectionError:
        logger.error("Failed to connect to OpenAI API")
        raise Exception("Failed to connect to AI service. Please check your internet connection.")
    
    except openai.AuthenticationError:
        logger.error("OpenAI API authentication failed")
        raise Exception("AI service authentication failed. Please check configuration.")
    
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
        "timestamp": datetime.utcnow().isoformat()
    })

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
    # Validate configuration before starting
    if not app.config['OPENAI_API_KEY']:
        logger.error("OPENAI_API_KEY not configured. Please check your .env file.")
        exit(1)
    
    logger.info(f"Starting Ruby's Gifts Flask server on {app.config['HOST']}:{app.config['PORT']}")
    logger.info(f"Debug mode: {app.config['DEBUG']}")
    
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )