"""Unit tests for util/auth.py"""
import pytest
import jwt
import time
from datetime import datetime, timedelta
from util.auth import (
    hash_password, 
    verify_password, 
    generate_token, 
    decode_token
)

class TestPasswordHashing:
    """Test cases for password hashing functionality."""
    
    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        password = "TestPassword123"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
    
    def test_hash_password_different_from_original(self):
        """Test that hashed password is different from original."""
        password = "TestPassword123"
        hashed = hash_password(password)
        assert hashed != password
    
    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salting)."""
        password = "TestPassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2, "Same password should produce different hashes due to salting"
    
    def test_hash_password_with_special_chars(self):
        """Test hashing password with special characters."""
        password = "Test@Pass#123!"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0


class TestPasswordVerification:
    """Test cases for password verification."""
    
    def test_verify_correct_password(self):
        """Test that correct password is verified successfully."""
        password = "TestPassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self):
        """Test that incorrect password is rejected."""
        password = "TestPassword123"
        wrong_password = "WrongPassword456"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "TestPassword123"
        hashed = hash_password(password)
        assert verify_password("testpassword123", hashed) is False
    
    def test_verify_empty_password(self):
        """Test verification with empty password."""
        password = "TestPassword123"
        hashed = hash_password(password)
        assert verify_password("", hashed) is False


class TestTokenGeneration:
    """Test cases for JWT token generation."""
    
    def test_generate_token_returns_string(self):
        """Test that generate_token returns a string."""
        token = generate_token("user123", "test@example.com")
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_token_contains_valid_payload(self):
        """Test that generated token contains correct payload."""
        user_id = "user123"
        email = "test@example.com"
        token = generate_token(user_id, email)
        
        # Decode without verification to check payload
        import os
        secret_key = os.getenv('JWT_SECRET_KEY', 'avirajkale50')
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        
        assert payload['user_id'] == user_id
        assert payload['email'] == email
        assert 'exp' in payload
        assert 'iat' in payload
    
    def test_token_expiration_set(self):
        """Test that token has expiration time set."""
        token = generate_token("user123", "test@example.com")
        
        import os
        secret_key = os.getenv('JWT_SECRET_KEY', 'avirajkale50')
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        
        exp_time = datetime.fromtimestamp(payload['exp'])
        iat_time = datetime.fromtimestamp(payload['iat'])
        
        # Token should expire in approximately 1 day
        time_diff = exp_time - iat_time
        assert time_diff.days == 1 or time_diff.seconds >= 86000  # ~1 day


class TestTokenDecoding:
    """Test cases for JWT token decoding."""
    
    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        user_id = "user123"
        email = "test@example.com"
        token = generate_token(user_id, email)
        
        payload = decode_token(token)
        assert payload is not None
        assert payload['user_id'] == user_id
        assert payload['email'] == email
    
    def test_decode_invalid_token(self):
        """Test decoding an invalid token."""
        invalid_token = "invalid.token.here"
        payload = decode_token(invalid_token)
        assert payload is None
    
    def test_decode_expired_token(self):
        """Test decoding an expired token."""
        import os
        secret_key = os.getenv('JWT_SECRET_KEY', 'avirajkale50')
        
        # Create token that expired 1 hour ago
        expired_payload = {
            'user_id': 'user123',
            'email': 'test@example.com',
            'exp': datetime.utcnow() - timedelta(hours=1),
            'iat': datetime.utcnow() - timedelta(hours=2)
        }
        expired_token = jwt.encode(expired_payload, secret_key, algorithm='HS256')
        
        payload = decode_token(expired_token)
        assert payload is None
    
    def test_decode_tampered_token(self):
        """Test decoding a tampered token."""
        token = generate_token("user123", "test@example.com")
        
        # Tamper with the token
        tampered_token = token[:-10] + "tampered12"
        
        payload = decode_token(tampered_token)
        assert payload is None
    
    def test_decode_empty_token(self):
        """Test decoding an empty token."""
        payload = decode_token("")
        assert payload is None
