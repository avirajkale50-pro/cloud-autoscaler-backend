from repo.db import db
from repo.models import Metric, ScalingDecision, Instance
from sqlalchemy import func
from datetime import datetime, timedelta
from util.logger import logger
from constants.service_constants import (
    SCALE_DOWN_CPU_THRESHOLD, SCALE_DOWN_MEMORY_THRESHOLD,
    SCALE_UP_THRESHOLD, SUSTAINED_DURATION_MINUTES,
    CAPACITY_MULTIPLIER_UP, CAPACITY_MULTIPLIER_DOWN,
    IQR_MULTIPLIER, IQR_MIN_DATA_DURATION_MINUTES
)

def check_sustained_usage(instance_id, cpu_threshold=None, memory_threshold=None, duration_minutes=5, above=True):
    """
    Check if CPU/memory usage has been sustained above or below thresholds for a given duration
    """
    cutoff_time = datetime.utcnow() - timedelta(minutes=duration_minutes)
    
    metrics = Metric.query.filter(
        Metric.instance_id == instance_id,
        Metric.timestamp >= cutoff_time
    ).order_by(Metric.timestamp.asc()).all()
    
    if len(metrics) < 3:  # Need at least 3 data points for sustained check
        return False, 0.0
    
    matching_count = 0
    total_count = len(metrics)
    
    for metric in metrics:
        condition_met = False
        
        if cpu_threshold is not None and metric.cpu_utilization is not None:
            if above:
                condition_met = metric.cpu_utilization > cpu_threshold
            else:
                condition_met = metric.cpu_utilization < cpu_threshold
        
        if memory_threshold is not None and metric.memory_usage is not None:
            if above:
                if cpu_threshold is not None:
                    condition_met = condition_met or metric.memory_usage > memory_threshold
                else:
                    condition_met = metric.memory_usage > memory_threshold
            else:
                if cpu_threshold is not None and metric.cpu_utilization is not None:
                    condition_met = metric.cpu_utilization < cpu_threshold and metric.memory_usage < memory_threshold
                else:
                    condition_met = metric.memory_usage < memory_threshold
        
        if condition_met:
            matching_count += 1
    
    percentage = (matching_count / total_count) * 100 if total_count > 0 else 0
    is_sustained = percentage >= 80
    
    return is_sustained, percentage

def calculate_metrics_mean(instance_id, time_window_minutes=5):
    """
    Calculate mean of CPU utilization and memory usage for an instance.
    Uses metrics from the last N minutes, excluding outlier metrics.
    Returns (cpu_mean, memory_mean, network_in_mean, network_out_mean) or None if no data.
    """
    cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
    
    metrics = Metric.query.filter(
        Metric.instance_id == instance_id,
        Metric.timestamp >= cutoff_time,
        Metric.is_outlier == False
    ).all()
    
    if not metrics:
        return None
    
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
    """
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
    
    # Priority 1: Scale down if BOTH CPU < SCALE_DOWN_CPU_THRESHOLD AND memory < SCALE_DOWN_MEMORY_THRESHOLD sustained for SUSTAINED_DURATION_MINUTES minutes
    if current_cpu is not None and current_memory is not None:
        is_sustained, percentage = check_sustained_usage(
            instance_id, 
            cpu_threshold=SCALE_DOWN_CPU_THRESHOLD, 
            memory_threshold=SCALE_DOWN_MEMORY_THRESHOLD, 
            duration_minutes=SUSTAINED_DURATION_MINUTES, 
            above=False
        )
        if is_sustained:
            decision = "scale_down"
            reason = f"Sustained scale down: CPU < {SCALE_DOWN_CPU_THRESHOLD}% AND Memory < {SCALE_DOWN_MEMORY_THRESHOLD}% for {percentage:.1f}% of last {SUSTAINED_DURATION_MINUTES} minutes (Current: CPU={current_cpu:.2f}%, Memory={current_memory:.2f}%)"
            is_outlier = True
            outlier_type = "scale_down"
    
    # Priority 2: Scale up if CPU > SCALE_UP_THRESHOLD% OR memory > SCALE_UP_THRESHOLD% sustained for SUSTAINED_DURATION_MINUTES minutes
    if decision is None:
        if current_cpu is not None:
            is_sustained, percentage = check_sustained_usage(
                instance_id, 
                cpu_threshold=SCALE_UP_THRESHOLD, 
                duration_minutes=SUSTAINED_DURATION_MINUTES, 
                above=True
            )
            if is_sustained:
                decision = "scale_up"
                reason = f"Sustained scale up: CPU > {SCALE_UP_THRESHOLD}% for {percentage:.1f}% of last {SUSTAINED_DURATION_MINUTES} minutes (Current: {current_cpu:.2f}%)"
                is_outlier = True
                outlier_type = "scale_up"
        
        if decision is None and current_memory is not None:
            is_sustained, percentage = check_sustained_usage(
                instance_id, 
                memory_threshold=SCALE_UP_THRESHOLD, 
                duration_minutes=SUSTAINED_DURATION_MINUTES, 
                above=True
            )
            if is_sustained:
                decision = "scale_up"
                reason = f"Sustained scale up: Memory > {SCALE_UP_THRESHOLD}% for {percentage:.1f}% of last {SUSTAINED_DURATION_MINUTES} minutes (Current: {current_memory:.2f}%)"
                is_outlier = True
                outlier_type = "scale_up"
    
    # Priority 3: Use IQR method for normal conditions considering all metrics
    if decision is None:
        # Check if we have enough historical data (at least 5 minutes)
        earliest_needed_time = datetime.utcnow() - timedelta(minutes=IQR_MIN_DATA_DURATION_MINUTES)
        
        # Check if the oldest metric is older than the required duration
        oldest_metric = Metric.query.filter(
            Metric.instance_id == instance_id
        ).order_by(Metric.timestamp.asc()).first()
        
        if not oldest_metric or oldest_metric.timestamp > earliest_needed_time:
             decision = "no_action"
             reason = f"Insufficient historical data duration. Need at least {IQR_MIN_DATA_DURATION_MINUTES} minutes of data for IQR analysis."
        else:
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)
        historical_metrics = Metric.query.filter(
            Metric.instance_id == instance_id,
            Metric.timestamp >= cutoff_time,
            Metric.is_outlier == False
        ).all()
        
        if len(historical_metrics) < 4:
            decision = "no_action"
            metric_info = []
            if current_cpu is not None:
                metric_info.append(f"CPU: {current_cpu:.2f}%")
            if current_memory is not None:
                metric_info.append(f"Memory: {current_memory:.2f}%")
            reason = f"Insufficient data for IQR analysis. Current metrics - {', '.join(metric_info)}"
        else:
            scale_up_votes = 0
            scale_down_votes = 0
            
            if current_cpu is not None:
                cpu_values = sorted([m.cpu_utilization for m in historical_metrics if m.cpu_utilization is not None])
                if len(cpu_values) >= 4:
                    n = len(cpu_values)
                    q1 = cpu_values[n // 4]
                    q3 = cpu_values[(3 * n) // 4]
                    iqr = q3 - q1
                    cpu_lower = q1 - IQR_MULTIPLIER * iqr
                    cpu_upper = q3 + IQR_MULTIPLIER * iqr
                    
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
                    mem_lower = q1 - IQR_MULTIPLIER * iqr
                    mem_upper = q3 + IQR_MULTIPLIER * iqr
                    
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
                    net_in_lower = q1 - IQR_MULTIPLIER * iqr
                    net_in_upper = q3 + IQR_MULTIPLIER * iqr
                    
                    if current_network_in > net_in_upper:
                        scale_up_votes += 1  # Network gets lower weight
                        reasons_list.append(f"Network In ({current_network_in:,} bytes) > upper bound ({net_in_upper:,.0f} bytes)")
                    elif current_network_in < net_in_lower:
                        scale_down_votes += 1
                        reasons_list.append(f"Network In ({current_network_in:,} bytes) < lower bound ({net_in_lower:,.0f} bytes)")
            
            # Network Out Analysis
            if current_network_out is not None:
                network_out_values = sorted([m.network_out for m in historical_metrics if m.network_out is not None])
                if len(network_out_values) >= 4:
                    n = len(network_out_values)
                    q1 = network_out_values[n // 4]
                    q3 = network_out_values[(3 * n) // 4]
                    iqr = q3 - q1
                    net_out_lower = q1 - IQR_MULTIPLIER * iqr
                    net_out_upper = q3 + IQR_MULTIPLIER * iqr
                    
                    if current_network_out > net_out_upper:
                        scale_up_votes += 1  # Network gets lower weight
                        reasons_list.append(f"Network Out ({current_network_out:,} bytes) > upper bound ({net_out_upper:,.0f} bytes)")
                    elif current_network_out < net_out_lower:
                        scale_down_votes += 1
                        reasons_list.append(f"Network Out ({current_network_out:,} bytes) < lower bound ({net_out_lower:,.0f} bytes)")
            
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
    
    instance = Instance.query.filter_by(instance_id=instance_id).filter(Instance.deleted_at.is_(None)).first()
    
    if not instance:
        logger.warning(f"Instance {instance_id} not found or deleted, skipping scaling decision")
        return False, "Instance not found"
    
    previous_decision = instance.last_decision
    is_state_change = (previous_decision != decision)
    
    if decision in ['scale_up', 'scale_down'] and is_state_change:
        try:
            if decision == 'scale_up':
                instance.cpu_capacity *= CAPACITY_MULTIPLIER_UP
                instance.memory_capacity *= CAPACITY_MULTIPLIER_UP
                instance.network_capacity *= CAPACITY_MULTIPLIER_UP
                instance.current_scale_level += 1
                logger.info(f"Scaled up {instance_id}: Level {instance.current_scale_level}, CPU capacity: {instance.cpu_capacity:.1f}%")
            elif decision == 'scale_down':
                instance.cpu_capacity *= CAPACITY_MULTIPLIER_DOWN
                instance.memory_capacity *= CAPACITY_MULTIPLIER_DOWN
                instance.network_capacity *= CAPACITY_MULTIPLIER_DOWN
                instance.current_scale_level -= 1
                logger.info(f"Scaled down {instance_id}: Level {instance.current_scale_level}, CPU capacity: {instance.cpu_capacity:.1f}%")
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update instance capacity: {e}")
    
    # Only save to database and log if state has changed
    if is_state_change:
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
            
            # Update instance's last decision
            instance.last_decision = decision
            
            db.session.commit()

            if previous_decision is None:
                logger.info(f"Initial scaling state for {instance_id}: {decision}")
            elif decision == 'no_action':
                logger.info(f"State change for {instance_id}: {previous_decision} → {decision} (returned to normal)")
            else:
                logger.info(f"State change for {instance_id}: {previous_decision} → {decision}")
            
            return True, scaling_decision
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save scaling decision: {e}")
            return False, str(e)
    else:
        logger.debug(f"No state change for {instance_id}, still in '{decision}' state")
        return True, f"No state change (still {decision})"


def process_all_monitored_instances():
    monitored_instances = Instance.query.filter_by(is_monitoring=True).filter(Instance.deleted_at.is_(None)).all()
    
    results = []
    for instance in monitored_instances:
        success, result = make_scaling_decision(instance.instance_id)
        results.append({
            'instance_id': instance.instance_id,
            'success': success,
            'result': result.decision if success and hasattr(result, 'decision') else result
        })
    
    return results
