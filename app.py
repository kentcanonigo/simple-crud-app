from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from dotenv import load_dotenv
from splunk_integration import create_splunk_integration
import time
import os
import pymysql
import logging

# Load environment variables from .env file
load_dotenv()

# Install PyMySQL as MySQLdb
pymysql.install_as_MySQLdb()

app = Flask(__name__)

# Database configuration with environment variables
DATABASE_TYPE = os.environ.get('DATABASE_TYPE', 'sqlite').lower()
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Use explicit DATABASE_URL if provided (overrides DATABASE_TYPE)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
elif DATABASE_TYPE == 'sqlite':
    # SQLite configuration
    db_file = os.environ.get('SQLITE_FILE', 'todos.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_file}'
elif DATABASE_TYPE == 'mysql':
    # MySQL configuration
    mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
    mysql_port = os.environ.get('MYSQL_PORT', '3306')
    mysql_user = os.environ.get('MYSQL_USER', 'todoapp')
    mysql_password = os.environ.get('MYSQL_PASSWORD', 'todoapp123')
    mysql_database = os.environ.get('MYSQL_DATABASE', 'todoapp')

    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}'
else:
    raise ValueError(f"Unsupported DATABASE_TYPE: {DATABASE_TYPE}. Use 'sqlite' or 'mysql'")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Prometheus metrics
REQUEST_COUNT = Counter('flask_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('flask_request_duration_seconds', 'Request latency')

# Initialize Splunk integration
splunk_hec, splunk_metrics_exporter, splunk_logger = create_splunk_integration()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    REQUEST_COUNT.labels(method=request.method, endpoint=request.endpoint).inc()
    request_latency = time.time() - request.start_time
    REQUEST_LATENCY.observe(request_latency)

    # Send request data to Splunk if configured
    if splunk_logger:
        try:
            splunk_logger.log_request(
                method=request.method,
                endpoint=request.endpoint or request.path,
                status_code=response.status_code,
                duration=request_latency
            )
        except Exception as e:
            logging.error(f"Failed to log request to Splunk: {e}")

    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/todos', methods=['GET'])
def get_todos():
    todos = Todo.query.all()
    return jsonify([todo.to_dict() for todo in todos])

@app.route('/api/todos', methods=['POST'])
def create_todo():
    data = request.get_json()

    if not data or 'title' not in data:
        if splunk_logger:
            splunk_logger.log_business_event("todo_creation_failed", {
                "reason": "missing_title",
                "request_data": data
            })
        return jsonify({'error': 'Title is required'}), 400

    todo = Todo(
        title=data['title'],
        description=data.get('description', ''),
        completed=data.get('completed', False)
    )

    try:
        db.session.add(todo)
        db.session.commit()

        # Log successful todo creation to Splunk
        if splunk_logger:
            splunk_logger.log_business_event("todo_created", {
                "todo_id": todo.id,
                "title": todo.title,
                "completed": todo.completed
            })
            splunk_logger.log_database_operation("INSERT", "todos", True)

        return jsonify(todo.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        if splunk_logger:
            splunk_logger.log_error("database_error", str(e), context={"operation": "create_todo"})
            splunk_logger.log_database_operation("INSERT", "todos", False)
        return jsonify({'error': 'Failed to create todo'}), 500

@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    todo.title = data.get('title', todo.title)
    todo.description = data.get('description', todo.description)
    todo.completed = data.get('completed', todo.completed)

    db.session.commit()

    return jsonify(todo.to_dict())

@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    db.session.delete(todo)
    db.session.commit()

    return jsonify({'message': 'Todo deleted successfully'}), 200

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/splunk/export-metrics', methods=['POST'])
def export_metrics_to_splunk():
    """Export Prometheus metrics to Splunk HEC"""
    if not splunk_metrics_exporter:
        return jsonify({
            'error': 'Splunk integration not configured',
            'message': 'Set SPLUNK_HEC_URL and SPLUNK_HEC_TOKEN environment variables'
        }), 400

    try:
        result = splunk_metrics_exporter.export_prometheus_metrics()
        return jsonify({
            'status': 'success',
            'exported_metrics': result['exported_count'],
            'errors': result['errors'],
            'timestamp': result['timestamp']
        }), 200
    except Exception as e:
        if splunk_logger:
            splunk_logger.log_error("metrics_export_error", str(e))
        return jsonify({'error': f'Failed to export metrics: {str(e)}'}), 500

@app.route('/splunk/test', methods=['POST'])
def test_splunk_connection():
    """Test Splunk HEC connection"""
    if not splunk_hec:
        return jsonify({
            'error': 'Splunk integration not configured',
            'message': 'Set SPLUNK_HEC_URL and SPLUNK_HEC_TOKEN environment variables'
        }), 400

    try:
        test_event = {
            "event_type": "connection_test",
            "app": "todoapp",
            "message": "Splunk HEC connection test",
            "test_timestamp": time.time()
        }

        success = splunk_hec.send_event(test_event)

        if success:
            return jsonify({
                'status': 'success',
                'message': 'Successfully connected to Splunk HEC'
            }), 200
        else:
            return jsonify({
                'status': 'failed',
                'message': 'Failed to send test event to Splunk HEC'
            }), 500

    except Exception as e:
        return jsonify({'error': f'Connection test failed: {str(e)}'}), 500

@app.route('/splunk/status')
def splunk_status():
    """Get Splunk integration status"""
    return jsonify({
        'splunk_configured': splunk_hec is not None,
        'metrics_exporter_available': splunk_metrics_exporter is not None,
        'logger_available': splunk_logger is not None,
        'configuration': {
            'hec_url_set': bool(os.environ.get('SPLUNK_HEC_URL')),
            'hec_token_set': bool(os.environ.get('SPLUNK_HEC_TOKEN')),
            'index': os.environ.get('SPLUNK_INDEX', 'main'),
            'source': os.environ.get('SPLUNK_SOURCE', 'todoapp')
        }
    })

def create_app():
    """Application factory pattern for better testability"""
    return app

def init_db():
    """Initialize database tables"""
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    # Only create tables in development mode
    # In production, use Flask-Migrate commands
    if os.environ.get('FLASK_ENV') != 'production':
        init_db()

    # Get port from environment variable for cloud deployment
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'

    app.run(debug=debug, host='0.0.0.0', port=port)