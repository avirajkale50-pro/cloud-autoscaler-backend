import re
from constants.validation_constants import EMAIL_REGEX, MIN_PASSWORD_LENGTH, PASSWORD_SPECIAL_CHARS

def validate_email(email):
    if not email:
        return False, "Email is required"
    
    if re.match(EMAIL_REGEX, email):
        return True, ""
    else:
        return False, "Invalid email format"

def validate_password(password):
    if not password:
        return False, "Password is required"
    
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
    
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one number"
        
    if not any(char.isalpha() for char in password):
        return False, "Password must contain at least one letter"

    if not any(char in PASSWORD_SPECIAL_CHARS for char in password):
        return False, f"Password must contain at least one special character ({PASSWORD_SPECIAL_CHARS})"
        
    return True, ""
