from flask import Blueprint, request, jsonify
from util.auth import token_required
from repo.models import Metric, ScalingDecision, Instance

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route('/<instance_id>', methods=['GET'])
@token_required
def get_instance_metrics(current_user, instance_id):
    """Get metrics for a specific instance."""
    user_id = current_user['user_id']
    
    # Verify instance ownership
    instance = Instance.query.filter_by(instance_id=instance_id).first()
    if not instance:
        return jsonify({'error': 'Instance not found'}), 404
    
    if str(instance.user_id) != str(user_id):
        return jsonify({'error': 'Unauthorized: You don\'t own this instance'}), 403
    
    # Get metrics
    limit = request.args.get('limit', 100, type=int)
    metrics = Metric.query.filter_by(instance_id=instance_id)\
        .order_by(Metric.timestamp.desc())\
        .limit(limit)\
        .all()
    
    return jsonify({
        'instance_id': instance_id,
        'metrics': [{
            'id': str(m.id),
            'timestamp': m.timestamp.isoformat(),
            'cpu_utilization': m.cpu_utilization,
            'memory_usage': m.memory_usage,
            'network_in': m.network_in,
            'network_out': m.network_out
        } for m in metrics]
    }), 200

@metrics_bp.route('/decisions/<instance_id>', methods=['GET'])
@token_required
def get_scaling_decisions(current_user, instance_id):
    """Get scaling decisions for a specific instance."""
    user_id = current_user['user_id']
    
    # Verify instance ownership
    instance = Instance.query.filter_by(instance_id=instance_id).first()
    if not instance:
        return jsonify({'error': 'Instance not found'}), 404
    
    if str(instance.user_id) != str(user_id):
        return jsonify({'error': 'Unauthorized: You don\'t own this instance'}), 403
    
    # Get decisions
    limit = request.args.get('limit', 50, type=int)
    decisions = ScalingDecision.query.filter_by(instance_id=instance_id)\
        .order_by(ScalingDecision.timestamp.desc())\
        .limit(limit)\
        .all()
    
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
        } for d in decisions]
    }), 200
