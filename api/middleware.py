from flask import request, jsonify, g
from functools import wraps
import jwt
import os
from datetime import datetime
from util.logger import logger

# Public routes that don't require authentication
PUBLIC_ROUTES = [
    '/api/',  # Health check
    '/api/auth/register',
    '/api/auth/login',
    '/api/docs',  # Swagger docs
    '/static/',  # Static files
]

def is_public_route(path):
    """Check if the route is public and doesn't require authentication."""
    # Exact match or prefix match for public routes
    for public_route in PUBLIC_ROUTES:
        if path == public_route or path.startswith(public_route):
            return True
    return False

def request_logging_middleware():
    """Log incoming requests with timestamp, method, path, and IP."""
    # Skip logging for static files and health checks to reduce noise
    if request.path.startswith('/static/') or request.path == '/api/':
        return
    
    logger.info(f"[{request.method}] {request.path} - IP: {request.remote_addr}")

def authentication_middleware():
    """
    Global authentication middleware that validates JWT tokens for protected routes.
    Public routes are excluded from authentication.
    """
    # Skip authentication for public routes
    if is_public_route(request.path):
        return
    
    # Skip for OPTIONS requests (CORS preflight)
    if request.method == 'OPTIONS':
        return
    
    token = None
    
    # Extract token from Authorization header
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        try:
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            else:
                logger.warning(f"Invalid Authorization header format from {request.remote_addr}")
                return jsonify({'error': 'Invalid token format. Use: Bearer <token>'}), 401
        except IndexError:
            logger.warning(f"Malformed Authorization header from {request.remote_addr}")
            return jsonify({'error': 'Malformed Authorization header'}), 401
    
    if not token:
        logger.warning(f"Missing token for protected route: {request.path} from {request.remote_addr}")
        return jsonify({'error': 'Authentication token is required'}), 401
    
    # Validate and decode token
    try:
        secret_key = os.getenv('JWT_SECRET_KEY', 'avirajkale50')
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        
        # Store user info in Flask's g object for access in route handlers
        g.current_user = {
            'user_id': payload.get('user_id'),
            'email': payload.get('email')
        }
        
        logger.debug(f"Authenticated user: {payload.get('email')} for {request.path}")
        
    except jwt.ExpiredSignatureError:
        logger.warning(f"Expired token used for {request.path} from {request.remote_addr}")
        return jsonify({'error': 'Token has expired. Please login again.'}), 401
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token for {request.path} from {request.remote_addr}: {str(e)}")
        return jsonify({'error': 'Invalid authentication token'}), 401
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return jsonify({'error': 'Authentication failed'}), 401

def response_logging_middleware(response):
    """Log response status codes for debugging."""
    # Skip logging for static files and successful health checks
    if request.path.startswith('/static/') or (request.path == '/api/' and response.status_code == 200):
        return response
    
    logger.info(f"[{request.method}] {request.path} - Status: {response.status_code}")
    return response

def error_handling_middleware(error):
    """
    Global error handler for unhandled exceptions.
    Logs the error and returns a consistent JSON response.
    """
    logger.error(f"Unhandled error on {request.path}: {str(error)}", exc_info=True)
    
    # Return a generic error message to the client
    return jsonify({
        'error': 'An internal server error occurred',
        'message': str(error) if os.getenv('FLASK_ENV') == 'development' else 'Please contact support'
    }), 500

def register_middleware(app):
    """
    Register all middleware with the Flask application.
    This function should be called in main.py during app initialization.
    """
    # Before request middleware (runs before each request)
    app.before_request(request_logging_middleware)
    app.before_request(authentication_middleware)
    
    # After request middleware (runs after each request)
    app.after_request(response_logging_middleware)
    
    # Error handlers
    app.errorhandler(Exception)(error_handling_middleware)
    
    # Specific error handlers for common HTTP errors
    @app.errorhandler(404)
    def not_found_error(error):
        logger.warning(f"404 Not Found: {request.path}")
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(405)
    def method_not_allowed_error(error):
        logger.warning(f"405 Method Not Allowed: {request.method} {request.path}")
        return jsonify({'error': f'Method {request.method} not allowed for this endpoint'}), 405
    
    @app.errorhandler(400)
    def bad_request_error(error):
        logger.warning(f"400 Bad Request: {request.path}")
        return jsonify({'error': 'Bad request', 'message': str(error)}), 400
    
    logger.info("Middleware registered successfully")
