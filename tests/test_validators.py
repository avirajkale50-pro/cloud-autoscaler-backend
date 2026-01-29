"""Unit tests for util/validators.py"""
import pytest
from util.validators import validate_email, validate_password

class TestEmailValidation:
    """Test cases for email validation."""
    
    def test_valid_emails(self):
        """Test that valid email formats are accepted."""
        valid_emails = [
            'test@example.com',
            'user.name@example.com',
            'user+tag@example.co.uk',
            'test123@test-domain.com',
            'a@b.co'
        ]
        
        for email in valid_emails:
            is_valid, message = validate_email(email)
            assert is_valid is True, f"Email {email} should be valid"
            assert message == ""
    
    def test_invalid_email_formats(self):
        """Test that invalid email formats are rejected."""
        invalid_emails = [
            'notanemail',
            '@example.com',
            'user@',
            'user @example.com',
            'user@.com',
            'user@example',
            ''
        ]
        
        for email in invalid_emails:
            is_valid, message = validate_email(email)
            assert is_valid is False, f"Email {email} should be invalid"
            assert message != ""
    
    def test_empty_email(self):
        """Test that empty email is rejected."""
        is_valid, message = validate_email('')
        assert is_valid is False
        assert message == "Email is required"
    
    def test_none_email(self):
        """Test that None email is rejected."""
        is_valid, message = validate_email(None)
        assert is_valid is False
        assert message == "Email is required"


class TestPasswordValidation:
    """Test cases for password validation."""
    
    def test_valid_passwords(self):
        """Test that valid passwords are accepted."""
        valid_passwords = [
            'Test@123',
            'MyP@ssw0rd',
            'Secure#Pass1',
            'C0mplex!Pass',
            'Valid$123Pass'
        ]
        
        for password in valid_passwords:
            is_valid, message = validate_password(password)
            assert is_valid is True, f"Password {password} should be valid"
            assert message == ""
    
    def test_password_too_short(self):
        """Test that passwords shorter than minimum length are rejected."""
        short_passwords = [
            'Ab@1',
            'Test@1',
            'A@1b'
        ]
        
        for password in short_passwords:
            is_valid, message = validate_password(password)
            assert is_valid is False
            assert "at least" in message.lower()
    
    def test_password_missing_number(self):
        """Test that passwords without numbers are rejected."""
        is_valid, message = validate_password('TestPassword@')
        assert is_valid is False
        assert "number" in message.lower()
    
    def test_password_missing_letter(self):
        """Test that passwords without letters are rejected."""
        is_valid, message = validate_password('12345@#$%')
        assert is_valid is False
        assert "letter" in message.lower()
    
    def test_password_missing_special_char(self):
        """Test that passwords without special characters are rejected."""
        is_valid, message = validate_password('TestPassword123')
        assert is_valid is False
        assert "special character" in message.lower()
    
    def test_empty_password(self):
        """Test that empty password is rejected."""
        is_valid, message = validate_password('')
        assert is_valid is False
        assert message == "Password is required"
    
    def test_none_password(self):
        """Test that None password is rejected."""
        is_valid, message = validate_password(None)
        assert is_valid is False
        assert message == "Password is required"
    
    def test_password_with_all_requirements(self):
        """Test password that meets all requirements."""
        is_valid, message = validate_password('MySecure@Pass123')
        assert is_valid is True
        assert message == ""
