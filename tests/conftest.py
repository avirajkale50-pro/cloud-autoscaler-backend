import pytest
import os
import sys
from datetime import datetime
from flask import Flask
import uuid

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from repo.db import db
from repo.models import User, Instance, Metric, ScalingDecision

@pytest.fixture(scope='function')
def app():
    """Create and configure a test Flask application."""
    from flask import Flask
    from flask_cors import CORS
    
    # Create minimal test app
    test_app = Flask(__name__)
    CORS(test_app)
    
    test_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',  # In-memory database for tests
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False
    })
    
    # Initialize Database
    db.init_app(test_app)
    
    # Register middleware and blueprints
    from api.middleware import register_middleware
    from api.routes import api_bp
    from api.auth_routes import auth_bp
    from api.instance_routes import instance_bp
    from api.metrics_routes import metrics_bp
    
    register_middleware(test_app)
    test_app.register_blueprint(api_bp, url_prefix='/api')
    test_app.register_blueprint(auth_bp, url_prefix='/api/auth')
    test_app.register_blueprint(instance_bp, url_prefix='/api/instances')
    test_app.register_blueprint(metrics_bp, url_prefix='/api/metrics')
    
    # Create application context and tables
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture(scope='function')
def sample_user(app):
    """Create a sample user for testing."""
    from util.auth import hash_password
    
    with app.app_context():
        user = User(
            email='test@example.com',
            password=hash_password('Test@123')
        )
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        
        # Return user data with UUID object
        user_data = {
            'id': user.id,  # Return UUID object, not string
            'id_str': str(user.id),  # Also provide string version
            'email': user.email,
            'password': 'Test@123'  # Plain password for login tests
        }
        
        yield user_data

@pytest.fixture(scope='function')
def sample_user_token(app, sample_user):
    """Generate a JWT token for the sample user."""
    from util.auth import generate_token
    with app.app_context():
        return generate_token(str(sample_user['id']), sample_user['email'])

@pytest.fixture(scope='function')
def sample_instance(app, sample_user):
    """Create a sample instance for testing."""
    with app.app_context():
        instance = Instance(
            instance_id='i-test123',
            instance_type='t2.micro',
            region='us-east-1',
            user_id=sample_user['id'],  # Use UUID object directly
            is_monitoring=False,
            is_mock=True
        )
        db.session.add(instance)
        db.session.commit()
        db.session.refresh(instance)
        
        instance_data = {
            'instance_id': instance.instance_id,
            'instance_type': instance.instance_type,
            'region': instance.region,
            'user_id': instance.user_id  # Return UUID object
        }
        
        yield instance_data

@pytest.fixture(scope='function')
def sample_metrics(app, sample_instance):
    """Create sample metrics for testing."""
    from datetime import timedelta
    
    with app.app_context():
        metrics = []
        base_time = datetime.utcnow()
        
        # Create 10 metrics over 5 minutes
        for i in range(10):
            metric = Metric(
                instance_id=sample_instance['instance_id'],
                cpu_utilization=45.0 + i * 2,  # Gradually increasing
                memory_usage=50.0 + i * 1.5,
                network_in=1000000 + i * 10000,
                network_out=500000 + i * 5000,
                timestamp=base_time - timedelta(minutes=9-i),
                is_outlier=False
            )
            metrics.append(metric)
            db.session.add(metric)
        
        db.session.commit()
        yield metrics

@pytest.fixture(scope='function')
def auth_headers(app, sample_user_token):
    """Create authorization headers with Bearer token."""
    with app.app_context():
        return {
            'Authorization': f'Bearer {sample_user_token}',
            'Content-Type': 'application/json'
        }
