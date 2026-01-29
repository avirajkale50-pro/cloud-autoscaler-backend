from flask import Blueprint, request, jsonify
from service.user_service import register_user, login_user
from util.validators import validate_email, validate_password
from util.auth import token_required
from repo.models import User, Instance
import jwt
from flask import current_app

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    is_valid_email, email_error = validate_email(email)
    if not is_valid_email:
        return jsonify({'error': email_error}), 400
        
    is_valid_password, password_error = validate_password(password)
    if not is_valid_password:
        return jsonify({'error': password_error}), 400
    
    success, result = register_user(email, password)
    
    if success:
        return jsonify({
            'message': 'User registered successfully',
            'user_id': result
        }), 201
    else:
        return jsonify({'error': result}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login and get JWT token."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    from util.validators import validate_email
    
    is_valid_email, email_error = validate_email(email)
    if not is_valid_email:
        return jsonify({'error': email_error}), 400
    
    success, result = login_user(email, password)
    
    if success:
        return jsonify({
            'message': 'Login successful',
            'token': result
        }), 200
    else:
        return jsonify({'error': result}), 401

@auth_bp.route('/me', methods=['GET'])
def get_user_info():
    """Get current user information."""
    
    token = None
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    
    if not token:
        return jsonify({'error': 'Token is missing'}), 401
    
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        user_id = payload['user_id']
        
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        total_instances = Instance.query.filter_by(user_id=user_id).count()
        monitoring_instances = Instance.query.filter_by(user_id=user_id, is_monitoring=True).count()
        
        return jsonify({
            'user_id': str(user.id),
            'email': user.email,
            'created_at': user.created_at.isoformat(),
            'instance_count': total_instances,
            'monitoring_count': monitoring_instances
        }), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

