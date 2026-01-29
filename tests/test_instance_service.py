"""Unit tests for service/instance_service.py"""
import pytest
from unittest.mock import patch, MagicMock
from service.instance_service import (
    register_instance,
    start_monitoring,
    stop_monitoring,
    get_user_instances,
    delete_instance
)
from repo.models import Instance
from repo.db import db
from datetime import datetime

class TestInstanceRegistration:
    """Test cases for instance registration."""
    
    def test_successful_mock_instance_registration(self, app, sample_user):
        """Test successful registration of a mock instance."""
        with app.app_context():
            instance_id = "i-mock-test-123"
            instance_type = "t2.micro"
            region = "us-east-1"
            
            success, result = register_instance(
                sample_user['id'], 
                instance_id, 
                instance_type, 
                region, 
                is_mock=True
            )
            
            assert success is True
            assert isinstance(result, Instance)
            assert result.instance_id == instance_id
            assert result.is_mock is True
            assert result.is_monitoring is False
            assert result.current_scale_level == 1
    
    def test_duplicate_instance_registration(self, app, sample_user, sample_instance):
        """Test that duplicate instance registration is rejected."""
        with app.app_context():
            instance_id = sample_instance['instance_id']
            
            success, result = register_instance(
                sample_user['id'],
                instance_id,
                "t2.small",
                "us-west-2",
                is_mock=True
            )
            
            assert success is False
            assert "already registered" in result.lower()
    
    @patch('service.instance_service.verify_connection')
    def test_real_instance_registration_with_verification(self, mock_verify, app, sample_user):
        """Test registration of real instance with AWS verification."""
        with app.app_context():
            # Mock successful AWS verification
            mock_verify.return_value = (True, "Verified")
            
            instance_id = "i-real-aws-123"
            instance_type = "t2.medium"
            region = "us-west-2"
            
            success, result = register_instance(
                sample_user['id'],
                instance_id,
                instance_type,
                region,
                is_mock=False
            )
            
            assert success is True
            assert isinstance(result, Instance)
            assert result.is_mock is False
            mock_verify.assert_called_once_with(instance_id, region)
    
    @patch('service.instance_service.verify_connection')
    def test_real_instance_registration_verification_failure(self, mock_verify, app, sample_user):
        """Test that registration fails when AWS verification fails."""
        with app.app_context():
            # Mock failed AWS verification
            mock_verify.return_value = (False, "Instance not found")
            
            instance_id = "i-nonexistent-123"
            
            success, result = register_instance(
                sample_user['id'],
                instance_id,
                "t2.micro",
                "us-east-1",
                is_mock=False
            )
            
            assert success is False
            assert "failed to verify" in result.lower()
    
    def test_instance_default_capacity_values(self, app, sample_user):
        """Test that instance is created with default capacity values."""
        with app.app_context():
            success, instance = register_instance(
                sample_user['id'],
                "i-capacity-test",
                "t2.micro",
                "us-east-1",
                is_mock=True
            )
            
            assert success is True
            assert instance.cpu_capacity == 100.0
            assert instance.memory_capacity == 100.0
            assert instance.network_capacity == 100.0


class TestStartMonitoring:
    """Test cases for starting instance monitoring."""
    
    def test_successful_start_monitoring(self, app, sample_user, sample_instance):
        """Test successfully starting monitoring for an instance."""
        with app.app_context():
            success, result = start_monitoring(
                sample_user['id'],
                sample_instance['instance_id']
            )
            
            assert success is True
            assert "started successfully" in result.lower()
            
            # Verify monitoring flag is set
            instance = Instance.query.filter_by(
                instance_id=sample_instance['instance_id']
            ).first()
            assert instance.is_monitoring is True
    
    def test_start_monitoring_already_active(self, app, sample_user, sample_instance):
        """Test that starting already active monitoring is rejected."""
        with app.app_context():
            # First start monitoring
            start_monitoring(sample_user['id'], sample_instance['instance_id'])
            
            # Try to start again
            success, result = start_monitoring(
                sample_user['id'],
                sample_instance['instance_id']
            )
            
            assert success is False
            assert "already active" in result.lower()
    
    def test_start_monitoring_unauthorized(self, app, sample_instance):
        """Test that unauthorized user cannot start monitoring."""
        with app.app_context():
            wrong_user_id = "different-user-id"
            
            success, result = start_monitoring(
                wrong_user_id,
                sample_instance['instance_id']
            )
            
            assert success is False
            assert "unauthorized" in result.lower()
    
    def test_start_monitoring_nonexistent_instance(self, app, sample_user):
        """Test starting monitoring for non-existent instance."""
        with app.app_context():
            success, result = start_monitoring(
                sample_user['id'],
                "i-nonexistent"
            )
            
            assert success is False
            assert "not found" in result.lower()


class TestStopMonitoring:
    """Test cases for stopping instance monitoring."""
    
    def test_successful_stop_monitoring(self, app, sample_user, sample_instance):
        """Test successfully stopping monitoring for an instance."""
        with app.app_context():
            # First start monitoring
            start_monitoring(sample_user['id'], sample_instance['instance_id'])
            
            # Then stop it
            success, result = stop_monitoring(
                sample_user['id'],
                sample_instance['instance_id']
            )
            
            assert success is True
            assert "stopped successfully" in result.lower()
            
            # Verify monitoring flag is unset
            instance = Instance.query.filter_by(
                instance_id=sample_instance['instance_id']
            ).first()
            assert instance.is_monitoring is False
    
    def test_stop_monitoring_not_active(self, app, sample_user, sample_instance):
        """Test that stopping inactive monitoring is rejected."""
        with app.app_context():
            success, result = stop_monitoring(
                sample_user['id'],
                sample_instance['instance_id']
            )
            
            assert success is False
            assert "not active" in result.lower()
    
    def test_stop_monitoring_unauthorized(self, app, sample_instance):
        """Test that unauthorized user cannot stop monitoring."""
        with app.app_context():
            wrong_user_id = "different-user-id"
            
            success, result = stop_monitoring(
                wrong_user_id,
                sample_instance['instance_id']
            )
            
            assert success is False
            assert "unauthorized" in result.lower()


class TestGetUserInstances:
    """Test cases for retrieving user instances."""
    
    def test_get_user_instances(self, app, sample_user, sample_instance):
        """Test retrieving instances for a user."""
        with app.app_context():
            instances = get_user_instances(sample_user['id'])
            
            assert len(instances) >= 1
            assert any(i.instance_id == sample_instance['instance_id'] for i in instances)
    
    def test_get_user_instances_excludes_deleted(self, app, sample_user):
        """Test that soft-deleted instances are excluded."""
        with app.app_context():
            # Create and soft-delete an instance
            instance = Instance(
                instance_id="i-deleted-test",
                instance_type="t2.micro",
                region="us-east-1",
                user_id=sample_user['id'],  # Use UUID object
                is_mock=True,
                deleted_at=datetime.utcnow()
            )
            db.session.add(instance)
            db.session.commit()
            
            # Get instances
            instances = get_user_instances(sample_user['id'])
            
            # Deleted instance should not be in results
            assert not any(i.instance_id == "i-deleted-test" for i in instances)
    
    def test_get_user_instances_empty(self, app):
        """Test retrieving instances for user with no instances."""
        with app.app_context():
            import uuid
            nonexistent_user_id = uuid.uuid4()
            instances = get_user_instances(nonexistent_user_id)
            assert len(instances) == 0


class TestDeleteInstance:
    """Test cases for deleting instances."""
    
    def test_successful_delete_instance(self, app, sample_user, sample_instance):
        """Test successfully soft-deleting an instance."""
        with app.app_context():
            success, result = delete_instance(
                sample_user['id'],
                sample_instance['instance_id']
            )
            
            assert success is True
            assert "deleted successfully" in result.lower()
            
            # Verify instance is soft-deleted
            instance = Instance.query.filter_by(
                instance_id=sample_instance['instance_id']
            ).first()
            assert instance.deleted_at is not None
    
    def test_delete_instance_while_monitoring(self, app, sample_user, sample_instance):
        """Test that instance cannot be deleted while monitoring is active."""
        with app.app_context():
            # Start monitoring
            start_monitoring(sample_user['id'], sample_instance['instance_id'])
            
            # Try to delete
            success, result = delete_instance(
                sample_user['id'],
                sample_instance['instance_id']
            )
            
            assert success is False
            assert "monitoring is active" in result.lower()
    
    def test_delete_instance_unauthorized(self, app, sample_instance):
        """Test that unauthorized user cannot delete instance."""
        with app.app_context():
            wrong_user_id = "different-user-id"
            
            success, result = delete_instance(
                wrong_user_id,
                sample_instance['instance_id']
            )
            
            assert success is False
            assert "unauthorized" in result.lower()
    
    def test_delete_nonexistent_instance(self, app, sample_user):
        """Test deleting non-existent instance."""
        with app.app_context():
            success, result = delete_instance(
                sample_user['id'],
                "i-nonexistent"
            )
            
            assert success is False
            assert "not found" in result.lower()
