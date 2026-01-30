from repo.db import db
from repo.models import Instance
from service.aws_monitor import verify_connection
from util.logger import logger
from datetime import datetime

def register_instance(user_id, instance_id, instance_type, region, is_mock=False):
    existing_instance = Instance.query.filter_by(instance_id=instance_id).filter(Instance.deleted_at.is_(None)).first()
    if existing_instance:
        return False, "Instance already registered"
    
    # For real instances, verify AWS connection
    if not is_mock:
        success, result = verify_connection(instance_id, region)
        if not success:
            return False, f"Failed to verify instance: {result}"
        logger.info(f"Verified instance {instance_id} in AWS")
    else:
        logger.info(f"Registering mock instance {instance_id}")
    
    # for now capacity is set to 100 
    new_instance = Instance(
        instance_id=instance_id,
        instance_type=instance_type,
        region=region,
        user_id=user_id,
        is_monitoring=False,
        is_mock=is_mock,
        cpu_capacity=100.0,
        memory_capacity=100.0,
        network_capacity=100.0,
        current_scale_level=1
    )
    
    try:
        db.session.add(new_instance)
        db.session.commit()
        return True, new_instance
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def start_monitoring(user_id, instance_id):
    instance = Instance.query.filter_by(instance_id=instance_id).first()
    
    if not instance:
        return False, "Instance not found"
    
    #who own the instance
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
    instance = Instance.query.filter_by(instance_id=instance_id).first()
    
    if not instance:
        return False, "Instance not found"
    
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
    Get all instances for a user (excluding soft-deleted instances).
    Returns list of instances.
    """
    instances = Instance.query.filter_by(user_id=user_id).filter(Instance.deleted_at.is_(None)).all()
    return instances

def delete_instance(user_id, instance_id):

    instance = Instance.query.filter_by(instance_id=instance_id).filter(Instance.deleted_at.is_(None)).first()
    
    if not instance:
        return False, "Instance not found"
    
    if str(instance.user_id) != str(user_id):
        return False, "Unauthorized: You don't own this instance"
    
    if instance.is_monitoring:
        return False, "Cannot delete instance while monitoring is active. Please stop monitoring first."
    
    instance.deleted_at = datetime.utcnow()
    
    try:
        db.session.commit()
        logger.info(f"Soft deleted instance {instance_id} for user {user_id}")
        return True, "Instance deleted successfully"
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete instance {instance_id}: {str(e)}")
        return False, str(e)

