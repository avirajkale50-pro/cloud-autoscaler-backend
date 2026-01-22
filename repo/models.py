from repo.db import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)  # Will store hashed password
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    instances = db.relationship('Instance', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'

class Instance(db.Model):
    __tablename__ = 'instances'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instance_id = db.Column(db.String, unique=True, nullable=False)
    instance_type = db.Column(db.String)
    region = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    is_monitoring = db.Column(db.Boolean, default=False)

    # Relationships
    metrics = db.relationship('Metric', backref='instance', lazy=True)
    decisions = db.relationship('ScalingDecision', backref='instance', lazy=True)

    def __repr__(self):
        return f'<Instance {self.instance_id}>'

class Metric(db.Model):
    __tablename__ = 'metrics'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instance_id = db.Column(db.String, db.ForeignKey('instances.instance_id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    cpu_utilization = db.Column(db.Float)
    memory_usage = db.Column(db.Float)
    network_in = db.Column(db.BigInteger)
    network_out = db.Column(db.BigInteger)
    
    # Outlier flags - metrics that triggered immediate scaling decisions
    is_outlier = db.Column(db.Boolean, default=False)
    outlier_type = db.Column(db.String)  # 'scale_up', 'scale_down', or None

    def __repr__(self):
        return f'<Metric {self.id}>'

class ScalingDecision(db.Model):
    __tablename__ = 'scaling_decisions'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instance_id = db.Column(db.String, db.ForeignKey('instances.instance_id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    cpu_utilization = db.Column(db.Float)
    memory_usage = db.Column(db.Float)
    network_in = db.Column(db.BigInteger)
    network_out = db.Column(db.BigInteger)
    
    decision = db.Column(db.String) # scale_up / scale_down / no_action
    reason = db.Column(db.Text)

    def __repr__(self):
        return f'<ScalingDecision {self.decision} for {self.instance_id}>'
