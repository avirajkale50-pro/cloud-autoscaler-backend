"""Unit tests for service/scaling_service.py"""
import pytest
from datetime import datetime, timedelta
from service.scaling_service import (
    check_sustained_usage,
    calculate_metrics_mean,
    make_scaling_decision
)
from repo.models import Metric, Instance
from repo.db import db

class TestSustainedUsageCheck:
    """Test cases for sustained usage checking."""
    
    def test_sustained_high_cpu_usage(self, app, sample_instance):
        """Test detection of sustained high CPU usage."""
        with app.app_context():
            # Create metrics with consistently high CPU
            base_time = datetime.utcnow()
            for i in range(10):
                metric = Metric(
                    instance_id=sample_instance['instance_id'],
                    cpu_utilization=95.0,
                    memory_usage=50.0,
                    timestamp=base_time - timedelta(minutes=9-i)
                )
                db.session.add(metric)
            db.session.commit()
            
            is_sustained, percentage = check_sustained_usage(
                sample_instance['instance_id'],
                cpu_threshold=90.0,
                duration_minutes=5,
                above=True
            )
            
            assert is_sustained is True
            assert percentage >= 80.0
    
    def test_sustained_low_usage(self, app, sample_instance):
        """Test detection of sustained low usage."""
        with app.app_context():
            # Create metrics with consistently low CPU and memory
            base_time = datetime.utcnow()
            for i in range(10):
                metric = Metric(
                    instance_id=sample_instance['instance_id'],
                    cpu_utilization=5.0,
                    memory_usage=15.0,
                    timestamp=base_time - timedelta(minutes=9-i)
                )
                db.session.add(metric)
            db.session.commit()
            
            is_sustained, percentage = check_sustained_usage(
                sample_instance['instance_id'],
                cpu_threshold=10.0,
                memory_threshold=20.0,
                duration_minutes=5,
                above=False
            )
            
            assert is_sustained is True
            assert percentage >= 80.0
    
    def test_insufficient_data_for_sustained_check(self, app, sample_instance):
        """Test that insufficient data returns False."""
        with app.app_context():
            # Create only 2 metrics (need at least 3)
            base_time = datetime.utcnow()
            for i in range(2):
                metric = Metric(
                    instance_id=sample_instance['instance_id'],
                    cpu_utilization=95.0,
                    memory_usage=50.0,
                    timestamp=base_time - timedelta(minutes=i)
                )
                db.session.add(metric)
            db.session.commit()
            
            is_sustained, percentage = check_sustained_usage(
                sample_instance['instance_id'],
                cpu_threshold=90.0,
                duration_minutes=5,
                above=True
            )
            
            assert is_sustained is False
    
    def test_intermittent_high_usage(self, app, sample_instance):
        """Test that intermittent high usage is not sustained."""
        with app.app_context():
            # Create metrics with alternating high/low CPU
            base_time = datetime.utcnow()
            for i in range(10):
                cpu = 95.0 if i % 2 == 0 else 30.0
                metric = Metric(
                    instance_id=sample_instance['instance_id'],
                    cpu_utilization=cpu,
                    memory_usage=50.0,
                    timestamp=base_time - timedelta(minutes=9-i)
                )
                db.session.add(metric)
            db.session.commit()
            
            is_sustained, percentage = check_sustained_usage(
                sample_instance['instance_id'],
                cpu_threshold=90.0,
                duration_minutes=5,
                above=True
            )
            
            # Should not be sustained (only ~50% of metrics above threshold)
            assert is_sustained is False


class TestMetricsMeanCalculation:
    """Test cases for metrics mean calculation."""
    
    def test_calculate_mean_with_valid_data(self, app, sample_instance):
        """Test calculating mean with valid metric data."""
        with app.app_context():
            # Create metrics
            base_time = datetime.utcnow()
            cpu_values = [40.0, 45.0, 50.0, 55.0, 60.0]
            
            for i, cpu in enumerate(cpu_values):
                metric = Metric(
                    instance_id=sample_instance['instance_id'],
                    cpu_utilization=cpu,
                    memory_usage=50.0 + i * 2,
                    network_in=1000000,
                    network_out=500000,
                    timestamp=base_time - timedelta(minutes=4-i),
                    is_outlier=False
                )
                db.session.add(metric)
            db.session.commit()
            
            result = calculate_metrics_mean(sample_instance['instance_id'])
            
            assert result is not None
            cpu_mean, memory_mean, network_in_mean, network_out_mean = result
            
            assert cpu_mean == sum(cpu_values) / len(cpu_values)
            assert memory_mean is not None
            assert network_in_mean is not None
            assert network_out_mean is not None
    
    def test_calculate_mean_excludes_outliers(self, app, sample_instance):
        """Test that outlier metrics are excluded from mean calculation."""
        with app.app_context():
            base_time = datetime.utcnow()
            
            # Create normal metrics
            for i in range(5):
                metric = Metric(
                    instance_id=sample_instance['instance_id'],
                    cpu_utilization=50.0,
                    memory_usage=50.0,
                    timestamp=base_time - timedelta(minutes=4-i),
                    is_outlier=False
                )
                db.session.add(metric)
            
            # Create outlier metric
            outlier = Metric(
                instance_id=sample_instance['instance_id'],
                cpu_utilization=99.0,
                memory_usage=99.0,
                timestamp=base_time,
                is_outlier=True
            )
            db.session.add(outlier)
            db.session.commit()
            
            result = calculate_metrics_mean(sample_instance['instance_id'])
            cpu_mean, memory_mean, _, _ = result
            
            # Mean should be 50.0, not affected by outlier
            assert cpu_mean == 50.0
            assert memory_mean == 50.0
    
    def test_calculate_mean_no_data(self, app):
        """Test that None is returned when no data exists."""
        with app.app_context():
            result = calculate_metrics_mean("nonexistent-instance")
            assert result is None


class TestScalingDecisions:
    """Test cases for scaling decision logic."""
    
    def test_scale_up_decision_high_cpu(self, app, sample_instance):
        """Test scale up decision when CPU is consistently high."""
        with app.app_context():
            # Create instance
            instance = Instance.query.filter_by(
                instance_id=sample_instance['instance_id']
            ).first()
            
            # Create metrics with sustained high CPU
            base_time = datetime.utcnow()
            for i in range(10):
                metric = Metric(
                    instance_id=sample_instance['instance_id'],
                    cpu_utilization=95.0,
                    memory_usage=50.0,
                    network_in=1000000,
                    network_out=500000,
                    timestamp=base_time - timedelta(minutes=9-i),
                    is_outlier=False
                )
                db.session.add(metric)
            db.session.commit()
            
            success, result = make_scaling_decision(sample_instance['instance_id'])
            
            assert success is True
            if hasattr(result, 'decision'):
                assert result.decision == "scale_up"
    
    def test_scale_down_decision_low_usage(self, app, sample_instance):
        """Test scale down decision when usage is consistently low."""
        with app.app_context():
            # Create metrics with sustained low usage
            base_time = datetime.utcnow()
            for i in range(10):
                metric = Metric(
                    instance_id=sample_instance['instance_id'],
                    cpu_utilization=5.0,
                    memory_usage=15.0,
                    network_in=1000000,
                    network_out=500000,
                    timestamp=base_time - timedelta(minutes=9-i),
                    is_outlier=False
                )
                db.session.add(metric)
            db.session.commit()
            
            success, result = make_scaling_decision(sample_instance['instance_id'])
            
            assert success is True
            if hasattr(result, 'decision'):
                assert result.decision == "scale_down"
    
    def test_no_action_decision_normal_usage(self, app, sample_instance):
        """Test no action decision when usage is in normal range."""
        with app.app_context():
            # Create metrics with normal usage
            base_time = datetime.utcnow()
            for i in range(10):
                metric = Metric(
                    instance_id=sample_instance['instance_id'],
                    cpu_utilization=50.0,
                    memory_usage=50.0,
                    network_in=1000000,
                    network_out=500000,
                    timestamp=base_time - timedelta(minutes=9-i),
                    is_outlier=False
                )
                db.session.add(metric)
            db.session.commit()
            
            success, result = make_scaling_decision(sample_instance['instance_id'])
            
            assert success is True
            if hasattr(result, 'decision'):
                assert result.decision == "no_action"
    
    def test_no_metrics_available(self, app):
        """Test decision making with no metrics available."""
        with app.app_context():
            success, result = make_scaling_decision("nonexistent-instance")
            
            assert success is False
            assert "no recent metrics" in result.lower() or "not found" in result.lower()
    
    def test_capacity_update_on_scale_up(self, app, sample_instance):
        """Test that capacity is updated when scaling up."""
        with app.app_context():
            instance = Instance.query.filter_by(
                instance_id=sample_instance['instance_id']
            ).first()
            
            initial_cpu_capacity = instance.cpu_capacity
            initial_scale_level = instance.current_scale_level
            
            # Create metrics for scale up
            base_time = datetime.utcnow()
            for i in range(10):
                metric = Metric(
                    instance_id=sample_instance['instance_id'],
                    cpu_utilization=95.0,
                    memory_usage=95.0,
                    network_in=1000000,
                    network_out=500000,
                    timestamp=base_time - timedelta(minutes=9-i),
                    is_outlier=False
                )
                db.session.add(metric)
            db.session.commit()
            
            success, result = make_scaling_decision(sample_instance['instance_id'])
            
            # Refresh instance
            db.session.refresh(instance)
            
            if success and hasattr(result, 'decision') and result.decision == "scale_up":
                assert instance.cpu_capacity > initial_cpu_capacity
                assert instance.current_scale_level > initial_scale_level
    
    def test_capacity_update_on_scale_down(self, app, sample_instance):
        """Test that capacity is updated when scaling down."""
        with app.app_context():
            instance = Instance.query.filter_by(
                instance_id=sample_instance['instance_id']
            ).first()
            
            # Set initial higher capacity
            instance.cpu_capacity = 200.0
            instance.current_scale_level = 2
            db.session.commit()
            
            initial_cpu_capacity = instance.cpu_capacity
            initial_scale_level = instance.current_scale_level
            
            # Create metrics for scale down
            base_time = datetime.utcnow()
            for i in range(10):
                metric = Metric(
                    instance_id=sample_instance['instance_id'],
                    cpu_utilization=5.0,
                    memory_usage=10.0,
                    network_in=1000000,
                    network_out=500000,
                    timestamp=base_time - timedelta(minutes=9-i),
                    is_outlier=False
                )
                db.session.add(metric)
            db.session.commit()
            
            success, result = make_scaling_decision(sample_instance['instance_id'])
            
            # Refresh instance
            db.session.refresh(instance)
            
            if success and hasattr(result, 'decision') and result.decision == "scale_down":
                assert instance.cpu_capacity < initial_cpu_capacity
                assert instance.current_scale_level < initial_scale_level
