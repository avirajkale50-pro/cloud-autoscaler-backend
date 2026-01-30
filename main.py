from flask import Flask
from api.routes import api_bp
from api.auth_routes import auth_bp
from api.instance_routes import instance_bp
from api.metrics_routes import metrics_bp
from api.middleware import register_middleware
from flask_cors import CORS
from repo.db import db
from dotenv import load_dotenv
import os
from flask_apscheduler import APScheduler
from flask_swagger_ui import get_swaggerui_blueprint
from repo.models import Instance, Metric
from util.logger import logger
from jobs.tasks import fetch_metrics_job, scaling_decision_job

load_dotenv()

scheduler = APScheduler()


def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Configure 
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'avirajkale50')
    db.init_app(app)
    register_middleware(app)
    
    # Initialize Scheduler
    # Only run scheduler in the main process
    # This prevents duplicate job executions when debug=True
    if not scheduler.running and os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
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
            seconds=60
        )
    
    # Register Blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(instance_bp, url_prefix='/api/instances')
    app.register_blueprint(metrics_bp, url_prefix='/api/metrics')
    
    # Swagger UI configuration
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.yaml'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "Cloud Resource Autoscaler API",
            'docExpansion': 'list',
            'defaultModelsExpandDepth': 3
        }
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    
    with app.app_context():
        from repo import models
        try:
            db.create_all()
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
