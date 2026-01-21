from repo.db import db
from repo.models import Metric, ScalingDecision, Instance
from sqlalchemy import func
from datetime import datetime, timedelta

def calculate_metrics_mean(instance_id, time_window_minutes=5):
    """
    Calculate mean of CPU utilization and memory usage for an instance.
    Uses metrics from the last N minutes.
    Returns (cpu_mean, memory_mean, network_in_mean, network_out_mean) or None if no data.
    """
    cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
    
    metrics = Metric.query.filter(
        Metric.instance_id == instance_id,
        Metric.timestamp >= cutoff_time
    ).all()
    
    if not metrics:
        return None
    
    # Calculate means
    cpu_values = [m.cpu_utilization for m in metrics if m.cpu_utilization is not None]
    memory_values = [m.memory_usage for m in metrics if m.memory_usage is not None]
    network_in_values = [m.network_in for m in metrics if m.network_in is not None]
    network_out_values = [m.network_out for m in metrics if m.network_out is not None]
    
    cpu_mean = sum(cpu_values) / len(cpu_values) if cpu_values else None
    memory_mean = sum(memory_values) / len(memory_values) if memory_values else None
    network_in_mean = sum(network_in_values) / len(network_in_values) if network_in_values else None
    network_out_mean = sum(network_out_values) / len(network_out_values) if network_out_values else None
    
    return cpu_mean, memory_mean, network_in_mean, network_out_mean

def make_scaling_decision(instance_id):
    """
    Make a scaling decision for an instance based on metrics.
    Decision logic: if current mean CPU is between (mean - 31) and (mean + 31), no action.
    If greater, scale up. If less, scale down.
    Returns (success, decision_object or error_message).
    """
    # Get recent metrics mean
    result = calculate_metrics_mean(instance_id)
    
    if result is None:
        return False, "No metrics available for decision making"
    
    cpu_mean, memory_mean, network_in_mean, network_out_mean = result
    
    if cpu_mean is None:
        return False, "No CPU metrics available for decision making"
    
    # Get historical mean (last 30 minutes for baseline)
    historical_result = calculate_metrics_mean(instance_id, time_window_minutes=30)
    
    if historical_result is None or historical_result[0] is None:
        # Not enough historical data, use current as baseline
        baseline_cpu = cpu_mean
    else:
        baseline_cpu = historical_result[0]
    
    # Decision logic
    lower_threshold = baseline_cpu - 31
    upper_threshold = baseline_cpu + 31
    
    if cpu_mean > upper_threshold:
        decision = "scale_up"
        reason = f"CPU utilization ({cpu_mean:.2f}%) exceeds upper threshold ({upper_threshold:.2f}%)"
    elif cpu_mean < lower_threshold:
        decision = "scale_down"
        reason = f"CPU utilization ({cpu_mean:.2f}%) is below lower threshold ({lower_threshold:.2f}%)"
    else:
        decision = "no_action"
        reason = f"CPU utilization ({cpu_mean:.2f}%) is within acceptable range ({lower_threshold:.2f}% - {upper_threshold:.2f}%)"
    
    # Create scaling decision record
    scaling_decision = ScalingDecision(
        instance_id=instance_id,
        cpu_utilization=cpu_mean,
        memory_usage=memory_mean,
        network_in=int(network_in_mean) if network_in_mean else None,
        network_out=int(network_out_mean) if network_out_mean else None,
        decision=decision,
        reason=reason
    )
    
    try:
        db.session.add(scaling_decision)
        db.session.commit()
        return True, scaling_decision
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def process_all_monitored_instances():
    """
    Process scaling decisions for all instances that are being monitored.
    This function is called by the scheduler every 15 seconds.
    """
    monitored_instances = Instance.query.filter_by(is_monitoring=True).all()
    
    results = []
    for instance in monitored_instances:
        success, result = make_scaling_decision(instance.instance_id)
        results.append({
            'instance_id': instance.instance_id,
            'success': success,
            'result': result.decision if success else result
        })
    
    return results
