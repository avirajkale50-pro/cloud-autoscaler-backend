"""Unit tests for service/user_service.py"""
import pytest
from service.user_service import register_user, login_user
from repo.models import User
from repo.db import db

class TestUserRegistration:
    """Test cases for user registration."""
    
    def test_successful_registration(self, app):
        """Test successful user registration."""
        with app.app_context():
            email = "newuser@example.com"
            password = "SecurePass@123"
            
            success, result = register_user(email, password)
            
            assert success is True
            assert result is not None  # Should return user_id
            
            # Verify user was created in database
            user = User.query.filter_by(email=email).first()
            assert user is not None
            assert user.email == email
            assert user.password != password  # Password should be hashed
    
    def test_duplicate_email_registration(self, app, sample_user):
        """Test that duplicate email registration is rejected."""
        with app.app_context():
            email = sample_user['email']
            password = "AnotherPass@123"
            
            success, result = register_user(email, password)
            
            assert success is False
            assert "already exists" in result.lower()
    
    def test_registration_with_short_password(self, app):
        """Test that registration with short password is rejected."""
        with app.app_context():
            email = "shortpass@example.com"
            password = "12345"  # Too short
            
            success, result = register_user(email, password)
            
            assert success is False
            assert "at least" in result.lower()
    
    def test_registration_password_hashing(self, app):
        """Test that password is properly hashed during registration."""
        with app.app_context():
            email = "hashtest@example.com"
            password = "TestHash@123"
            
            success, result = register_user(email, password)
            
            assert success is True
            
            # Verify password is hashed
            user = User.query.filter_by(email=email).first()
            assert user.password != password
            assert len(user.password) > 20  # Hashed password should be longer
    
    def test_registration_returns_user_id(self, app):
        """Test that successful registration returns user ID."""
        with app.app_context():
            email = "userid@example.com"
            password = "ValidPass@123"
            
            success, user_id = register_user(email, password)
            
            assert success is True
            assert user_id is not None
            assert len(user_id) > 0
            
            # Verify the returned ID matches the created user
            user = User.query.filter_by(email=email).first()
            assert str(user.id) == user_id


class TestUserLogin:
    """Test cases for user login."""
    
    def test_successful_login(self, app, sample_user):
        """Test successful login with valid credentials."""
        with app.app_context():
            email = sample_user['email']
            password = sample_user['password']
            
            success, result = login_user(email, password)
            
            assert success is True
            assert result is not None  # Should return token
            assert len(result) > 0  # Token should be non-empty string
    
    def test_login_with_invalid_email(self, app):
        """Test login with non-existent email."""
        with app.app_context():
            email = "nonexistent@example.com"
            password = "AnyPassword@123"
            
            success, result = login_user(email, password)
            
            assert success is False
            assert "invalid" in result.lower()
    
    def test_login_with_wrong_password(self, app, sample_user):
        """Test login with incorrect password."""
        with app.app_context():
            email = sample_user['email']
            wrong_password = "WrongPass@123"
            
            success, result = login_user(email, wrong_password)
            
            assert success is False
            assert "invalid" in result.lower()
    
    def test_login_returns_valid_token(self, app, sample_user):
        """Test that login returns a valid JWT token."""
        with app.app_context():
            email = sample_user['email']
            password = sample_user['password']
            
            success, token = login_user(email, password)
            
            assert success is True
            
            # Verify token can be decoded
            from util.auth import decode_token
            payload = decode_token(token)
            
            assert payload is not None
            assert payload['email'] == email
            assert payload['user_id'] == sample_user['id_str']  # Use string version for comparison
    
    def test_login_case_sensitive_email(self, app, sample_user):
        """Test that email matching is case-sensitive."""
        with app.app_context():
            # Try login with uppercase email
            email_upper = sample_user['email'].upper()
            password = sample_user['password']
            
            success, result = login_user(email_upper, password)
            
            # This should fail if email is case-sensitive
            # If your implementation is case-insensitive, adjust this test
            assert success is False
    
    def test_login_with_empty_credentials(self, app):
        """Test login with empty email and password."""
        with app.app_context():
            success, result = login_user("", "")
            assert success is False
