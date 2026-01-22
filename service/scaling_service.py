from repo.db import db
from repo.models import Metric, ScalingDecision, Instance
from sqlalchemy import func
from datetime import datetime, timedelta
from util.logger import logger

def calculate_metrics_mean(instance_id, time_window_minutes=5):
    """
    Calculate mean of CPU utilization and memory usage for an instance.
    Uses metrics from the last N minutes, excluding outlier metrics.
    Returns (cpu_mean, memory_mean, network_in_mean, network_out_mean) or None if no data.
    """
    cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
    
    # Filter out outlier metrics to prevent skewing the baseline
    metrics = Metric.query.filter(
        Metric.instance_id == instance_id,
        Metric.timestamp >= cutoff_time,
        Metric.is_outlier == False
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
    Make a scaling decision for an instance based on multiple metrics.
    
    Decision logic (priority order):
    1. Immediate scale down if CPU < 10% AND memory < 20%
    2. Immediate scale up if CPU > 90% OR memory > 90%
    3. Use IQR (Interquartile Range) method for outlier detection considering all metrics
    
    Returns (success, decision_object or error_message).
    """
    # Get the most recent metric (current state)
    latest_metric = Metric.query.filter_by(instance_id=instance_id)\
        .order_by(Metric.timestamp.desc())\
        .first()
    
    if not latest_metric:
        return False, "No recent metrics available for decision making"
    
    current_cpu = latest_metric.cpu_utilization
    current_memory = latest_metric.memory_usage
    current_network_in = latest_metric.network_in
    current_network_out = latest_metric.network_out
    
    # Get recent metrics mean (excluding outliers)
    result = calculate_metrics_mean(instance_id)
    
    if result is None:
        cpu_mean, memory_mean, network_in_mean, network_out_mean = None, None, None, None
    else:
        cpu_mean, memory_mean, network_in_mean, network_out_mean = result
    
    decision = None
    reason = None
    is_outlier = False
    outlier_type = None
    reasons_list = []
    
    # Priority 1: Immediate scale down if BOTH CPU < 10% AND memory < 20%
    if current_cpu is not None and current_memory is not None:
        if current_cpu < 10 and current_memory < 20:
            decision = "scale_down"
            reason = f"Immediate scale down: CPU ({current_cpu:.2f}%) < 10% AND Memory ({current_memory:.2f}%) < 20%"
            is_outlier = True
            outlier_type = "scale_down"
    
    # Priority 2: Immediate scale up if CPU > 90% OR memory > 90%
    if decision is None:
        if current_cpu is not None and current_cpu > 90:
            decision = "scale_up"
            reason = f"Immediate scale up: CPU utilization ({current_cpu:.2f}%) exceeds 90% threshold"
            is_outlier = True
            outlier_type = "scale_up"
        elif current_memory is not None and current_memory > 90:
            decision = "scale_up"
            reason = f"Immediate scale up: Memory usage ({current_memory:.2f}%) exceeds 90% threshold"
            is_outlier = True
            outlier_type = "scale_up"
    
    # Priority 3: Use IQR method for normal conditions considering all metrics
    if decision is None:
        # Get historical metrics for IQR calculation (last 5 minutes, excluding outliers)
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)
        historical_metrics = Metric.query.filter(
            Metric.instance_id == instance_id,
            Metric.timestamp >= cutoff_time,
            Metric.is_outlier == False
        ).all()
        
        if len(historical_metrics) < 4:
            # Not enough data for IQR
            decision = "no_action"
            metric_info = []
            if current_cpu is not None:
                metric_info.append(f"CPU: {current_cpu:.2f}%")
            if current_memory is not None:
                metric_info.append(f"Memory: {current_memory:.2f}%")
            reason = f"Insufficient data for IQR analysis. Current metrics - {', '.join(metric_info)}"
        else:
            # Analyze each metric using IQR
            scale_up_votes = 0
            scale_down_votes = 0
            
            # CPU Analysis
            if current_cpu is not None:
                cpu_values = sorted([m.cpu_utilization for m in historical_metrics if m.cpu_utilization is not None])
                if len(cpu_values) >= 4:
                    n = len(cpu_values)
                    q1 = cpu_values[n // 4]
                    q3 = cpu_values[(3 * n) // 4]
                    iqr = q3 - q1
                    cpu_lower = q1 - 1.5 * iqr
                    cpu_upper = q3 + 1.5 * iqr
                    
                    if current_cpu > cpu_upper:
                        scale_up_votes += 2  # CPU gets higher weight
                        reasons_list.append(f"CPU ({current_cpu:.2f}%) > upper bound ({cpu_upper:.2f}%)")
                    elif current_cpu < cpu_lower:
                        scale_down_votes += 2
                        reasons_list.append(f"CPU ({current_cpu:.2f}%) < lower bound ({cpu_lower:.2f}%)")
            
            # Memory Analysis
            if current_memory is not None:
                memory_values = sorted([m.memory_usage for m in historical_metrics if m.memory_usage is not None])
                if len(memory_values) >= 4:
                    n = len(memory_values)
                    q1 = memory_values[n // 4]
                    q3 = memory_values[(3 * n) // 4]
                    iqr = q3 - q1
                    mem_lower = q1 - 1.5 * iqr
                    mem_upper = q3 + 1.5 * iqr
                    
                    if current_memory > mem_upper:
                        scale_up_votes += 2  # Memory gets higher weight
                        reasons_list.append(f"Memory ({current_memory:.2f}%) > upper bound ({mem_upper:.2f}%)")
                    elif current_memory < mem_lower:
                        scale_down_votes += 2
                        reasons_list.append(f"Memory ({current_memory:.2f}%) < lower bound ({mem_lower:.2f}%)")
            
            # Network In Analysis
            if current_network_in is not None:
                network_in_values = sorted([m.network_in for m in historical_metrics if m.network_in is not None])
                if len(network_in_values) >= 4:
                    n = len(network_in_values)
                    q1 = network_in_values[n // 4]
                    q3 = network_in_values[(3 * n) // 4]
                    iqr = q3 - q1
                    net_in_upper = q3 + 1.5 * iqr
                    
                    if current_network_in > net_in_upper:
                        scale_up_votes += 1  # Network gets lower weight
                        reasons_list.append(f"Network In ({current_network_in:,} bytes) > upper bound ({net_in_upper:,.0f} bytes)")
            
            # Network Out Analysis
            if current_network_out is not None:
                network_out_values = sorted([m.network_out for m in historical_metrics if m.network_out is not None])
                if len(network_out_values) >= 4:
                    n = len(network_out_values)
                    q1 = network_out_values[n // 4]
                    q3 = network_out_values[(3 * n) // 4]
                    iqr = q3 - q1
                    net_out_upper = q3 + 1.5 * iqr
                    
                    if current_network_out > net_out_upper:
                        scale_up_votes += 1  # Network gets lower weight
                        reasons_list.append(f"Network Out ({current_network_out:,} bytes) > upper bound ({net_out_upper:,.0f} bytes)")
            
            # Make decision based on votes (need at least 2 votes to trigger scaling)
            if scale_up_votes >= 2:
                decision = "scale_up"
                reason = f"Scale up recommended. Reasons: {'; '.join(reasons_list)}"
            elif scale_down_votes >= 2:
                decision = "scale_down"
                reason = f"Scale down recommended. Reasons: {'; '.join(reasons_list)}"
            else:
                decision = "no_action"
                metric_info = []
                if current_cpu is not None:
                    metric_info.append(f"CPU: {current_cpu:.2f}%")
                if current_memory is not None:
                    metric_info.append(f"Memory: {current_memory:.2f}%")
                reason = f"All metrics within acceptable range. Current: {', '.join(metric_info)}"
    
    # Flag the latest metric if it's an outlier
    if is_outlier:
        try:
            latest_metric.is_outlier = True
            latest_metric.outlier_type = outlier_type
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.warning(f"Could not flag metric as outlier: {e}")
    
    scaling_decision = ScalingDecision(
        instance_id=instance_id,
        cpu_utilization=current_cpu,
        memory_usage=current_memory,
        network_in=current_network_in,
        network_out=current_network_out,
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
