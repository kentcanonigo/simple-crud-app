from flask import Flask, request, jsonify, render_template, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from dotenv import load_dotenv
from structured_logging import setup_structured_logging, StructuredLogger
import time
import os
import pymysql
import logging
import uuid
from sqlalchemy import text

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
REQUEST_COUNT = Counter('todoapp_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('todoapp_request_duration_seconds', 'Request latency')

# Configure structured logging for Kubernetes/Splunk
setup_structured_logging()
structured_logger = StructuredLogger('todoapp')

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
    g.request_id = str(uuid.uuid4())

@app.after_request
def after_request(response):
    REQUEST_COUNT.labels(method=request.method, endpoint=request.endpoint).inc()
    request_latency = time.time() - request.start_time
    REQUEST_LATENCY.observe(request_latency)

    # Log request with structured logging
    try:
        structured_logger.log_request(
            method=request.method,
            endpoint=request.endpoint or request.path,
            status_code=response.status_code,
            duration=request_latency,
            log_level='INFO'
        )
    except Exception as e:
        logging.error(f"Failed to log request: {e}")

    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/todos', methods=['GET'], endpoint='get_todos_api')
def get_todos():
    todos = Todo.query.all()
    return jsonify([todo.to_dict() for todo in todos])

@app.route('/api/todos', methods=['POST'])
def create_todo():
    data = request.get_json()

    if not data or 'title' not in data:
        structured_logger.log_business_event("todo_creation_failed", {
            "reason": "missing_title",
            "request_data": data
        }, log_level='WARN')
        return jsonify({'error': 'Title is required'}), 400

    todo = Todo(
        title=data['title'],
        description=data.get('description', ''),
        completed=data.get('completed', False)
    )

    try:
        db.session.add(todo)
        db.session.commit()

        # Log successful todo creation
        structured_logger.log_business_event("todo_created", {
            "todo_id": todo.id,
            "title": todo.title,
            "completed": todo.completed
        }, log_level='INFO')
        structured_logger.log_database_operation("INSERT", "todos", True, log_level='INFO')

        return jsonify(todo.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        structured_logger.log_error("database_error", str(e), context={"operation": "create_todo"}, log_level='CRITICAL')
        structured_logger.log_database_operation("INSERT", "todos", False, log_level='CRITICAL')
        return jsonify({'error': 'Failed to create todo'}), 500

@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    old_values = {
        'title': todo.title,
        'description': todo.description,
        'completed': todo.completed
    }

    todo.title = data.get('title', todo.title)
    todo.description = data.get('description', todo.description)
    todo.completed = data.get('completed', todo.completed)

    try:
        db.session.commit()

        # Log successful update
        structured_logger.log_business_event("todo_updated", {
            "todo_id": todo.id,
            "old_values": old_values,
            "new_values": {
                'title': todo.title,
                'description': todo.description,
                'completed': todo.completed
            }
        }, log_level='INFO')
        structured_logger.log_database_operation("UPDATE", "todos", True, log_level='INFO')

        return jsonify(todo.to_dict())

    except Exception as e:
        db.session.rollback()
        structured_logger.log_error("database_error", str(e), context={"operation": "update_todo", "todo_id": todo_id}, log_level='CRITICAL')
        structured_logger.log_database_operation("UPDATE", "todos", False, log_level='CRITICAL')
        return jsonify({'error': 'Failed to update todo'}), 500

@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    todo_data = {
        'id': todo.id,
        'title': todo.title,
        'completed': todo.completed
    }

    try:
        db.session.delete(todo)
        db.session.commit()

        # Log successful deletion
        structured_logger.log_business_event("todo_deleted", {
            "todo_id": todo_id,
            "deleted_todo": todo_data
        }, log_level='INFO')
        structured_logger.log_database_operation("DELETE", "todos", True, log_level='INFO')

        return jsonify({'message': 'Todo deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        structured_logger.log_error("database_error", str(e), context={"operation": "delete_todo", "todo_id": todo_id}, log_level='CRITICAL')
        structured_logger.log_database_operation("DELETE", "todos", False, log_level='CRITICAL')
        return jsonify({'error': 'Failed to delete todo'}), 500

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    health_data = {
        'status': 'healthy' if db_status == 'healthy' else 'unhealthy',
        'database': db_status,
        'timestamp': time.time(),
        'version': '1.0.0'
    }

    # Log health check
    try:
        structured_logger.log_business_event("health_check", health_data, log_level='DEBUG')
    except Exception as e:
        logging.error(f"Failed to log health check: {e}")

    status_code = 200 if health_data['status'] == 'healthy' else 503
    return jsonify(health_data), status_code

@app.route('/simulate/404')
def simulate_404():
    """Simulate a 404 error for testing"""
    structured_logger.log_business_event("simulated_error", {
        "error_type": "404",
        "endpoint": "/simulate/404",
        "message": "Simulated 404 error for testing"
    }, log_level='DEV')

    return jsonify({'error': 'Resource not found', 'simulated': True}), 404

@app.route('/simulate/500')
def simulate_500():
    """Simulate a 500 error for testing"""
    structured_logger.log_business_event("simulated_error", {
        "error_type": "500",
        "endpoint": "/simulate/500",
        "message": "Simulated 500 error for testing"
    }, log_level='DEV')

    return jsonify({'error': 'Internal server error', 'simulated': True}), 500

@app.route('/simulate/timeout')
def simulate_timeout():
    """Simulate a slow response for testing"""
    import time
    structured_logger.log_business_event("simulated_slow_response", {
        "endpoint": "/simulate/timeout",
        "delay_seconds": 5,
        "message": "Simulated slow response for testing"
    }, log_level='DEV')

    time.sleep(5)  # 5 second delay
    return jsonify({'message': 'Slow response completed', 'delay': '5 seconds', 'simulated': True}), 200

@app.route('/simulate/database-error')
def simulate_database_error():
    """Simulate a database error for testing"""
    structured_logger.log_business_event("simulated_error", {
        "error_type": "database",
        "endpoint": "/simulate/database-error",
        "message": "Simulated database error for testing"
    }, log_level='DEV')
    structured_logger.log_database_operation("SELECT", "invalid_table", False, log_level='DEV')

    return jsonify({'error': 'Database connection failed', 'simulated': True}), 503

@app.route('/simulate/auth-error')
def simulate_auth_error():
    """Simulate an authentication error for testing"""
    structured_logger.log_business_event("simulated_error", {
        "error_type": "401",
        "endpoint": "/simulate/auth-error",
        "message": "Simulated authentication error for testing"
    }, log_level='DEV')

    return jsonify({'error': 'Authentication required', 'simulated': True}), 401

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