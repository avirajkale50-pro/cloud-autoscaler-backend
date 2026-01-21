from flask import Flask
from api.routes import api_bp
from api.auth_routes import auth_bp
from api.instance_routes import instance_bp
from api.metrics_routes import metrics_bp
from repo.db import db
from dotenv import load_dotenv
import os
from flask_apscheduler import APScheduler
from service.aws_monitor import fetch_instance_metrics
from service.scaling_service import process_all_monitored_instances
from repo.models import Instance, Metric

load_dotenv()

scheduler = APScheduler()

def fetch_metrics_job(app):
    """Job to fetch metrics for all instances that are being monitored."""
    with app.app_context():
        print("Running fetch_metrics_job...")
        # Only fetch metrics for instances with is_monitoring=True
        instances = Instance.query.filter_by(is_monitoring=True).all()
        
        if not instances:
            print("No instances are currently being monitored.")
            return
        
        for instance in instances:
            print(f"Fetching metrics for {instance.instance_id}...")
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
                   print(f"Saved metrics for {instance.instance_id}")
                else:
                    print(f"No metrics found for {instance.instance_id}")
            else:
                 print(f"Failed to fetch metrics for {instance.instance_id}")
        
        try:
            db.session.commit()
        except Exception as e:
            print(f"Error saving metrics: {e}")
            db.session.rollback()

def scaling_decision_job(app):
    """Job to make scaling decisions for all monitored instances."""
    with app.app_context():
        print("Running scaling_decision_job...")
        results = process_all_monitored_instances()
        
        for result in results:
            if result['success']:
                print(f"Decision for {result['instance_id']}: {result['result']}")
            else:
                print(f"Failed to make decision for {result['instance_id']}: {result['result']}")

def create_app():
    app = Flask(__name__)
    
    # Configure Database
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configure JWT Secret Key
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    
    # Initialize Database
    db.init_app(app)
    
    # Initialize Scheduler
    if not scheduler.running:
        scheduler.init_app(app)
        scheduler.start()
        
        # Add metrics fetching job (every 30 seconds)
        scheduler.add_job(
            id='fetch_metrics',
            func=fetch_metrics_job,
            args=[app],
            trigger='interval',
            seconds=30
        )
        
        # Add scaling decision job (every 15 seconds)
        scheduler.add_job(
            id='scaling_decisions',
            func=scaling_decision_job,
            args=[app],
            trigger='interval',
            seconds=15
        )
    
    # Register Blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(instance_bp, url_prefix='/api/instances')
    app.register_blueprint(metrics_bp, url_prefix='/api/metrics')
    
    with app.app_context():
        # Import models to ensure they are registered with SQLAlchemy
        from repo import models
        # Create tables
        try:
            db.create_all()
            print("Database connected and tables created (if not exist).")
        except Exception as e:
            print(f"Error connecting to database: {e}")
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
