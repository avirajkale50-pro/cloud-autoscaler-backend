from repo.db import db
from repo.models import Instance
from service.aws_monitor import verify_connection

def register_instance(user_id, instance_id, instance_type, region):
    """
    Register a new instance for a user.
    Returns (success, result) where result is instance object or error message.
    """
    # Check if instance already exists
    existing_instance = Instance.query.filter_by(instance_id=instance_id).first()
    if existing_instance:
        return False, "Instance already registered"
    
    # Verify AWS connection
    success, result = verify_connection(instance_id, region)
    if not success:
        return False, f"Failed to verify instance: {result}"
    
    # Create instance
    new_instance = Instance(
        instance_id=instance_id,
        instance_type=instance_type,
        region=region,
        user_id=user_id,
        is_monitoring=False
    )
    
    try:
        db.session.add(new_instance)
        db.session.commit()
        return True, new_instance
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def start_monitoring(user_id, instance_id):
    """
    Start monitoring for an instance.
    Returns (success, message).
    """
    instance = Instance.query.filter_by(instance_id=instance_id).first()
    
    if not instance:
        return False, "Instance not found"
    
    # Check ownership
    if str(instance.user_id) != str(user_id):
        return False, "Unauthorized: You don't own this instance"
    
    if instance.is_monitoring:
        return False, "Monitoring is already active for this instance"
    
    instance.is_monitoring = True
    
    try:
        db.session.commit()
        return True, "Monitoring started successfully"
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def stop_monitoring(user_id, instance_id):
    """
    Stop monitoring for an instance.
    Returns (success, message).
    """
    instance = Instance.query.filter_by(instance_id=instance_id).first()
    
    if not instance:
        return False, "Instance not found"
    
    # Check ownership
    if str(instance.user_id) != str(user_id):
        return False, "Unauthorized: You don't own this instance"
    
    if not instance.is_monitoring:
        return False, "Monitoring is not active for this instance"
    
    instance.is_monitoring = False
    
    try:
        db.session.commit()
        return True, "Monitoring stopped successfully"
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def get_user_instances(user_id):
    """
    Get all instances for a user.
    Returns list of instances.
    """
    instances = Instance.query.filter_by(user_id=user_id).all()
    return instances
