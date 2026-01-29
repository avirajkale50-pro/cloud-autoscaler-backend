from flask import Blueprint, jsonify, request
from repo.db import db
from repo.models import Instance
from service.aws_monitor import verify_connection

api_bp = Blueprint('api', __name__)

@api_bp.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Backend is running"})

@api_bp.route('/instances', methods=['POST'])
def register_instance():
    data = request.get_json()
    instance_id = data.get('instance_id')
    instance_type = data.get('instance_type')
    region = data.get('region')
    
    if not all([instance_id, instance_type, region]):
        return jsonify({"error": "Missing required fields"}), 400
        
    success, result = verify_connection(instance_id, region)
    if not success:
        return jsonify({"error": f"Failed to verify instance: {result}"}), 400
        
    try:
        new_instance = Instance(
            instance_id=instance_id,
            instance_type=instance_type,
            region=region
        )
        db.session.add(new_instance)
        db.session.commit()
        return jsonify({"message": "Monitoring started", "instance": instance_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
