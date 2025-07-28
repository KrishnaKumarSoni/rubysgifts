# Ruby's Gifts Flask Backend

A Flask-based REST API service that generates personalized gift recommendations using OpenAI's GPT-4o-mini model. Built for the Ruby's Gifts web application with comprehensive input validation, error handling, and CORS support.

## Features

- **RESTful API**: Clean `/generate_gifts` endpoint for gift generation
- **OpenAI Integration**: Uses GPT-4o-mini for creative, personalized suggestions
- **Robust Validation**: Comprehensive input sanitization and validation
- **Error Handling**: Detailed error responses with proper HTTP status codes
- **CORS Support**: Ready for frontend integration
- **Security**: Environment-based configuration, input sanitization
- **Logging**: Comprehensive logging for debugging and monitoring
- **Production Ready**: Structured code with proper configuration management

## Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone and navigate to the project**:
   ```bash
   cd rubysgifts
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

4. **Run the server**:
   ```bash
   python app.py
   ```

The server will start on `http://localhost:5000`

## API Documentation

### Health Check
```http
GET /
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Ruby's Gifts API",
  "version": "1.0.0",
  "timestamp": "2024-01-20T10:30:00.000Z"
}
```

### Generate Gift Ideas
```http
POST /generate_gifts
Content-Type: application/json
```

**Request Body:**
```json
{
  "call_them": "buddy",
  "relationship": "best friend",
  "previous_gifts": "chocolate, book, coffee mug",
  "hate": "spiders, loud noises, cheap plastic",
  "complaints": "traffic, work stress, bad weather",
  "complain_about_them": "always late, too picky, loud chewer",
  "budget": "under 500₹",
  "limitations": "allergy-free, eco-friendly, portable"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "gift_ideas": [
    {
      "title": "Personalized Stress-Relief Kit",
      "description": "A curated collection of natural stress-relief items...",
      "starter": "I noticed you've been stressed about work lately...",
      "reaction": "They'll appreciate the thoughtfulness and practical nature..."
    },
    {
      "title": "Eco-Friendly Travel Organizer",
      "description": "A sustainable, compact organizer perfect for someone always on the go...",
      "starter": "Since you're always rushing around, I thought this might help...",
      "reaction": "They'll love how it helps them stay organized..."
    },
    {
      "title": "Premium Noise-Canceling Earbuds",
      "description": "High-quality earbuds that block out unwanted noise...",
      "starter": "I remember you mentioning how much you hate loud noises...",
      "reaction": "They'll be amazed by the peace and quiet..."
    }
  ],
  "timestamp": "2024-01-20T10:30:00.000Z"
}
```

**Error Response (400/500):**
```json
{
  "success": false,
  "error": "Missing or empty responses for: call_them, relationship",
  "code": "INVALID_INPUT"
}
```

## Required Fields

All fields are required for the `/generate_gifts` endpoint:

- `call_them`: What you call the recipient
- `relationship`: Your relationship with them
- `previous_gifts`: Gifts you've given them before
- `hate`: Things they absolutely hate
- `complaints`: What they complain about
- `complain_about_them`: Their quirks/habits you'd complain about
- `budget`: Your budget range
- `limitations`: Any constraints (allergies, preferences, etc.)

## Configuration

Environment variables (in `.env` file):

- `OPENAI_API_KEY` (required): Your OpenAI API key
- `FLASK_DEBUG` (optional): Set to 'true' for debug mode
- `PORT` (optional): Server port (default: 5000)
- `HOST` (optional): Server host (default: 0.0.0.0)

## Error Codes

- `INVALID_CONTENT_TYPE`: Request missing JSON content-type
- `INVALID_INPUT`: Missing required fields or invalid data
- `INVALID_AI_RESPONSE`: Malformed response from OpenAI
- `INCOMPLETE_AI_RESPONSE`: Missing required fields in AI response
- `INTERNAL_ERROR`: Server error
- `NOT_FOUND`: Endpoint not found
- `METHOD_NOT_ALLOWED`: HTTP method not allowed

## Development

### Project Structure
```
rubysgifts/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── .env.example       # Environment template
├── .env               # Your environment variables (not in git)
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

### Key Components

- **Input Validation**: Comprehensive validation of all questionnaire data
- **Sanitization**: Basic XSS protection and input cleaning
- **OpenAI Integration**: Structured prompts for consistent gift generation
- **Error Handling**: Specific error handling for different failure scenarios
- **Logging**: Detailed logging for debugging and monitoring

### Adding Features

The codebase is structured for easy extension:

1. **New Endpoints**: Add to `app.py` following the existing pattern
2. **Validation**: Update `validate_questionnaire_data()` function
3. **AI Prompts**: Modify `create_gift_generation_prompt()` function
4. **Error Handling**: Add new error codes and handlers as needed

## Production Deployment

For production deployment:

1. **Use a production WSGI server**:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **Set environment variables**:
   ```bash
   export FLASK_DEBUG=false
   export OPENAI_API_KEY=your_production_key
   ```

3. **Consider adding**:
   - Rate limiting (flask-limiter)
   - Caching (Redis)
   - Database for logging
   - Load balancing
   - SSL certificates

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**:
   - Ensure your API key is correctly set in `.env`
   - Check you have sufficient OpenAI credits

2. **CORS Issues**:
   - Verify your frontend origin is in the CORS allowed origins
   - Check browser developer tools for CORS errors

3. **Import Errors**:
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check you're using Python 3.8+

4. **Port Already in Use**:
   - Change the PORT in `.env` file
   - Or kill the process using the port

### Logs

The application logs to stdout with timestamps. Key events logged:
- Server startup
- API requests
- OpenAI API calls
- Errors and warnings

## Support

For issues or questions about the Ruby's Gifts backend, check:
1. Application logs for error details
2. OpenAI API status if generation fails
3. Network connectivity for API calls

---

Built with Flask and OpenAI for the Ruby's Gifts web application.