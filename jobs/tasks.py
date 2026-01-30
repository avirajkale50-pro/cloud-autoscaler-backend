from repo.models import Instance, Metric
from repo.db import db
from util.logger import logger
from service.mock_monitor import generate_mock_metrics
from service.aws_monitor import fetch_instance_metrics
from service.scaling_service import process_all_monitored_instances

def fetch_metrics_job(app):
    """Job to fetch metrics for all instances that are being monitored."""
    with app.app_context():
        monitored_count = Instance.query.filter_by(is_monitoring=True).count()
        
        if monitored_count == 0:
            return
        
        logger.debug(f"Running fetch_metrics_job for {monitored_count} instance(s)...")
        instances = Instance.query.filter_by(is_monitoring=True).all()
        
        for instance in instances:
            logger.debug(f"Fetching metrics for {instance.instance_id}...")
            
            # Use mock data for mock instances, real AWS data for regular instances
            if instance.is_mock:
                logger.debug(f"Using mock data for {instance.instance_id}")
                metrics_data = generate_mock_metrics(instance.instance_id)
            else:
                metrics_data = fetch_instance_metrics(instance.instance_id, instance.region)
            
            if metrics_data:
                # Check if we got at least one metric
                if any(v is not None for v in metrics_data.values()):
                   new_metric = Metric(
                       instance_id=instance.instance_id,
                       cpu_utilization=metrics_data.get('cpu_utilization'),
                       memory_usage=metrics_data.get('memory_usage'),
                       network_in=metrics_data.get('network_in'),
                       network_out=metrics_data.get('network_out')
                   )
                   db.session.add(new_metric)
                   logger.info(f"Saved metrics for {instance.instance_id}")
                else:
                    logger.warning(f"No metrics found for {instance.instance_id}")
            else:
                 logger.error(f"Failed to fetch metrics for {instance.instance_id}")
        
        try:
            db.session.commit()
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            db.session.rollback()

def scaling_decision_job(app):
    """Job to make scaling decisions for all monitored instances."""
    with app.app_context():
        # Check if any instances are being monitored before running the job
        monitored_count = Instance.query.filter_by(is_monitoring=True).count()
        
        if monitored_count == 0:
            # Skip job execution - no instances to monitor
            return
        
        logger.debug(f"Running scaling_decision_job for {monitored_count} instance(s)...")
        results = process_all_monitored_instances()
        
        for result in results:
            if result['success']:
                logger.debug(f"Decision for {result['instance_id']}: {result['result']}")
            else:
                logger.error(f"Failed to make decision for {result['instance_id']}: {result['result']}")
