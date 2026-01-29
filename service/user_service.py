from repo.db import db
from repo.models import User
from util.auth import hash_password, verify_password, generate_token

def register_user(email, password):
    """
    Register a new user.
    Returns (success, result) where result is user_id or error message.
    """
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return False, "User with this email already exists"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    # Hash password and create user
    hashed_pw = hash_password(password)
    new_user = User(email=email, password=hashed_pw)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return True, str(new_user.id)
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def login_user(email, password):
    """
    Authenticate a user and return JWT token.
    Returns (success, result) where result is token or error message.
    """
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return False, "Invalid email or password"
    
    if not verify_password(password, user.password):
        return False, "Invalid email or password"
    
    # Generate token
    token = generate_token(user.id, user.email)
    return True, token
