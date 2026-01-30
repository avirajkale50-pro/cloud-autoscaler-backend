from flask import Blueprint, request, jsonify
from util.auth import token_required
from repo.models import Metric, ScalingDecision, Instance

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route('/<instance_id>', methods=['GET'])
@token_required
def get_instance_metrics(current_user, instance_id):
    """
    Get metrics for a specific instance with pagination support.
    
    Query Parameters:
        - page (int, optional): Page number (1-indexed, default: 1)
        - page_size (int, optional): Number of items per page (default: 10, max: 100)
        - limit (int, optional): Legacy parameter for backward compatibility (overrides page_size)
    """
    user_id = current_user['user_id']
    
    # Verify the instance who is the owner
    instance = Instance.query.filter_by(instance_id=instance_id).first()
    if not instance:
        return jsonify({'error': 'Instance not found'}), 404
    
    if str(instance.user_id) != str(user_id):
        return jsonify({'error': 'Unauthorized: You don\'t own this instance'}), 403
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    
    # Support legacy 'limit' parameter for backward compatibility
    if 'limit' in request.args:
        page_size = request.args.get('limit', 10, type=int)
        page = 1  # Reset to first page when using limit
    
    # Validate pagination parameters
    if page < 1:
        return jsonify({'error': 'Page must be >= 1'}), 400
    if page_size < 1 or page_size > 100:
        return jsonify({'error': 'Page size must be between 1 and 100'}), 400
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get total count
    total_count = Metric.query.filter_by(instance_id=instance_id).count()
    
    # Get metrics with pagination
    metrics = Metric.query.filter_by(instance_id=instance_id)\
        .order_by(Metric.timestamp.desc())\
        .limit(page_size)\
        .offset(offset)\
        .all()
    
    # Calculate pagination metadata
    total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
    has_next = page < total_pages
    has_prev = page > 1
    
    return jsonify({
        'instance_id': instance_id,
        'metrics': [{
            'id': str(m.id),
            'timestamp': m.timestamp.isoformat(),
            'cpu_utilization': m.cpu_utilization,
            'memory_usage': m.memory_usage,
            'network_in': m.network_in,
            'network_out': m.network_out,
            'is_outlier': m.is_outlier,
            'outlier_type': m.outlier_type
        } for m in metrics],
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_prev': has_prev
        }
    }), 200

@metrics_bp.route('/decisions/<instance_id>', methods=['GET'])
@token_required
def get_scaling_decisions(current_user, instance_id):
    """
    Get scaling decisions for a specific instance with pagination support.
    
    Query Parameters:
        - page (int, optional): Page number (1-indexed, default: 1)
        - page_size (int, optional): Number of items per page (default: 10, max: 100)
        - limit (int, optional): Legacy parameter for backward compatibility (overrides page_size)
    """
    user_id = current_user['user_id']
    
    instance = Instance.query.filter_by(instance_id=instance_id).first()
    if not instance:
        return jsonify({'error': 'Instance not found'}), 404
    
    if str(instance.user_id) != str(user_id):
        return jsonify({'error': 'Unauthorized: You don\'t own this instance'}), 403
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    
    # Support legacy 'limit' parameter for backward compatibility
    if 'limit' in request.args:
        page_size = request.args.get('limit', 10, type=int)
        page = 1  # Reset to first page when using limit
    
    # Validate pagination parameters
    if page < 1:
        return jsonify({'error': 'Page must be >= 1'}), 400
    if page_size < 1 or page_size > 100:
        return jsonify({'error': 'Page size must be between 1 and 100'}), 400
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get total count
    total_count = ScalingDecision.query.filter_by(instance_id=instance_id).count()
    
    # Get decisions with pagination
    decisions = ScalingDecision.query.filter_by(instance_id=instance_id)\
        .order_by(ScalingDecision.timestamp.desc())\
        .limit(page_size)\
        .offset(offset)\
        .all()
    
    # Calculate pagination metadata
    total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
    has_next = page < total_pages
    has_prev = page > 1
    
    return jsonify({
        'instance_id': instance_id,
        'decisions': [{
            'id': str(d.id),
            'timestamp': d.timestamp.isoformat(),
            'cpu_utilization': d.cpu_utilization,
            'memory_usage': d.memory_usage,
            'network_in': d.network_in,
            'network_out': d.network_out,
            'decision': d.decision,
            'reason': d.reason
        } for d in decisions],
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_prev': has_prev
        }
    }), 200

@metrics_bp.route('/simulate', methods=['POST'])
@token_required
def simulate_metrics(current_user):
    """
    Simulate metrics for testing purposes.
    
    Supports two modes:
    1. Instant simulation: Create a single metric with provided values
    2. Prolonged simulation: Create multiple metrics over a duration with specified interval
    
    Parameters:
        - instance_id (required): Instance to simulate metrics for
        - cpu_utilization (optional): CPU percentage
        - memory_usage (optional): Memory percentage
        - network_in (optional): Network in bytes
        - network_out (optional): Network out bytes
        - duration_minutes (optional): Duration in minutes for prolonged simulation
        - interval_seconds (optional): Interval between metrics in seconds (default: 30)
    """
    from repo.db import db
    from datetime import datetime, timedelta
    import time
    
    user_id = current_user['user_id']
    data = request.get_json()

    if not data or 'instance_id' not in data:
        return jsonify({'error': 'instance_id is required'}), 400
    
    instance_id = data['instance_id']

    instance = Instance.query.filter_by(instance_id=instance_id).first()
    if not instance:
        return jsonify({'error': 'Instance not found'}), 404
    
    if str(instance.user_id) != str(user_id):
        return jsonify({'error': 'Unauthorized: You don\'t own this instance'}), 403

    cpu_utilization = data.get('cpu_utilization')
    memory_usage = data.get('memory_usage')
    network_in = data.get('network_in')
    network_out = data.get('network_out')
    duration_minutes = data.get('duration_minutes')
    interval_seconds = data.get('interval_seconds', 30)
    clear_existing = data.get('clear_existing', False)  # New parameter to clear old metrics
    
    created_metrics = []
    
    try:
        # Clear existing metrics if requested
        if clear_existing:
            deleted_count = Metric.query.filter_by(instance_id=instance_id).delete()
            db.session.commit()
            logger.info(f"Cleared {deleted_count} existing metrics for {instance_id} before simulation")
        
        if duration_minutes:
            num_metrics = int((duration_minutes * 60) / interval_seconds)
            start_time = datetime.utcnow()
            
            for i in range(num_metrics):
                metric_timestamp = start_time - timedelta(seconds=(num_metrics - i - 1) * interval_seconds)
                
                metric = Metric(
                    instance_id=instance_id,
                    cpu_utilization=cpu_utilization,
                    memory_usage=memory_usage,
                    network_in=network_in,
                    network_out=network_out,
                    timestamp=metric_timestamp
                )
                db.session.add(metric)
                created_metrics.append({
                    'timestamp': metric_timestamp.isoformat(),
                    'cpu_utilization': cpu_utilization,
                    'memory_usage': memory_usage
                })
            
            db.session.commit()
            
            return jsonify({
                'message': f'Created {num_metrics} simulated metrics over {duration_minutes} minutes',
                'metrics_created': num_metrics,
                'duration_minutes': duration_minutes,
                'interval_seconds': interval_seconds,
                'sample_metrics': created_metrics[:3]
            }), 201
        else:
            metric = Metric(
                instance_id=instance_id,
                cpu_utilization=cpu_utilization,
                memory_usage=memory_usage,
                network_in=network_in,
                network_out=network_out
            )
            
            db.session.add(metric)
            db.session.commit()
            
            return jsonify({
                'message': 'Simulated metric created successfully',
                'metric': {
                    'id': str(metric.id),
                    'instance_id': metric.instance_id,
                    'timestamp': metric.timestamp.isoformat(),
                    'cpu_utilization': metric.cpu_utilization,
                    'memory_usage': metric.memory_usage,
                    'network_in': metric.network_in,
                    'network_out': metric.network_out,
                    'is_outlier': metric.is_outlier,
                    'outlier_type': metric.outlier_type
                }
            }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create metric: {str(e)}'}), 500

