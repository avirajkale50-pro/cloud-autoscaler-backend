from flask import Blueprint, request, jsonify
from util.auth import token_required
from service.instance_service import register_instance, start_monitoring, stop_monitoring, get_user_instances, delete_instance

instance_bp = Blueprint('instances', __name__)

@instance_bp.route('/', methods=['POST'])
@token_required
def create_instance(current_user):
    """Register a new instance for the authenticated user."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    instance_id = data.get('instance_id')
    instance_type = data.get('instance_type')
    region = data.get('region')
    is_mock = data.get('is_mock', False)
    
    if not all([instance_id, instance_type, region]):
        return jsonify({'error': 'instance_id, instance_type, and region are required'}), 400
    
    user_id = current_user['user_id']
    success, result = register_instance(user_id, instance_id, instance_type, region, is_mock)
    
    if success:
        return jsonify({
            'message': 'Instance registered successfully',
            'instance': {
                'id': str(result.id),
                'instance_id': result.instance_id,
                'instance_type': result.instance_type,
                'region': result.region,
                'is_monitoring': result.is_monitoring,
                'is_mock': result.is_mock
            }
        }), 201
    else:
        return jsonify({'error': result}), 400

@instance_bp.route('/', methods=['GET'])
@token_required
def get_instances(current_user):
    """Get all instances for the authenticated user."""
    user_id = current_user['user_id']
    instances = get_user_instances(user_id)
    
    return jsonify({
        'instances': [{
            'id': str(inst.id),
            'instance_id': inst.instance_id,
            'instance_type': inst.instance_type,
            'region': inst.region,
            'is_monitoring': inst.is_monitoring,
            'is_mock': inst.is_mock,
            'created_at': inst.created_at.isoformat()
        } for inst in instances]
    }), 200

@instance_bp.route('/<instance_id>/monitor/start', methods=['PATCH'])
@token_required
def start_instance_monitoring(current_user, instance_id):
    """Start monitoring for a specific instance."""
    user_id = current_user['user_id']
    success, message = start_monitoring(user_id, instance_id)
    
    if success:
        return jsonify({'message': message}), 200
    else:
        return jsonify({'error': message}), 400

@instance_bp.route('/<instance_id>/monitor/stop', methods=['PATCH'])
@token_required
def stop_instance_monitoring(current_user, instance_id):
    """Stop monitoring for a specific instance."""
    user_id = current_user['user_id']
    success, message = stop_monitoring(user_id, instance_id)
    
    if success:
        return jsonify({'message': message}), 200
    else:
        return jsonify({'error': message}), 400

@instance_bp.route('/<instance_id>', methods=['DELETE'])
@token_required
def delete_instance_route(current_user, instance_id):
    """Delete an instance (soft delete)"""
    user_id = current_user['user_id']
    success, message = delete_instance(user_id, instance_id)
    
    if success:
        return jsonify({'message': message}), 200
    else:
        if "not found" in message.lower():
            return jsonify({'error': message}), 404
        elif "unauthorized" in message.lower():
            return jsonify({'error': message}), 403
        else:
            return jsonify({'error': message}), 400
