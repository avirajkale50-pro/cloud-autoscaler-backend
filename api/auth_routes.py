from flask import Blueprint, request, jsonify
from service.user_service import register_user, login_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
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
    
    success, result = login_user(email, password)
    
    if success:
        return jsonify({
            'message': 'Login successful',
            'token': result
        }), 200
    else:
        return jsonify({'error': result}), 401
