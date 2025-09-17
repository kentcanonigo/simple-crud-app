# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Local development with Docker Compose:**
```bash
docker-compose up -d
```

**Local development without Docker:**
```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your MySQL settings

# Install dependencies
pip install -r requirements.txt

# Run with MySQL
python app.py
```

**Database migrations:**
```bash
# Initialize migrations (first time)
flask db init

# Create migration
flask db migrate -m "Description"

# Apply migration
flask db upgrade
```

**Kubernetes deployment:**
```bash
# Update database-url secret in k8s-deployment.yaml
kubectl apply -f k8s-deployment.yaml
```

**Access points:**
- Web UI: http://localhost:5000
- API endpoints: http://localhost:5000/api/todos
- Prometheus metrics: http://localhost:5000/metrics
- Splunk status: http://localhost:5000/splunk/status
- Splunk metrics export: POST http://localhost:5000/splunk/export-metrics
- Splunk connection test: POST http://localhost:5000/splunk/test

## Architecture Overview

Production-ready Flask todo application with MySQL backend:

**Core Components:**
- `app.py`: Flask application with MySQL configuration and environment-based settings
- `templates/index.html`: Bootstrap frontend with embedded JavaScript for API interaction
- MySQL database with connection pooling and health checks

**Key Architecture Patterns:**
- **Environment-based configuration**: Database settings via environment variables or DATABASE_URL
- **Production deployment ready**: Docker, Kubernetes, and database migration support
- **Connection pooling**: MySQL connection pool with pre-ping and recycling
- **REST API design**: `/api/todos` endpoints follow REST conventions
- **Flask-Migrate integration**: Database schema versioning for production deployments
- **Prometheus integration**: Request metrics automatically collected via before/after request hooks
- **Splunk integration**: HTTP Event Collector (HEC) for logs and metrics export

**Database Configuration:**
- **Development**: Uses individual MySQL environment variables (MYSQL_HOST, MYSQL_USER, etc.)
- **Production**: Uses single DATABASE_URL for cloud deployment compatibility
- **Connection options**: Pool pre-ping and 300s recycle for reliability

**Data Flow:**
1. Frontend JavaScript makes AJAX calls to `/api/todos` endpoints
2. Flask routes handle CRUD operations via SQLAlchemy with MySQL
3. All requests/responses automatically tracked for Prometheus metrics
4. Database operations use Flask-SQLAlchemy with connection pooling

**Database Schema:**
- Single `Todo` table with: id, title, description, completed, created_at
- MySQL database with proper indexing and constraints
- Schema managed via Flask-Migrate for version control

**Deployment Options:**
- **Docker Compose**: Full stack with MySQL for local development
- **Kubernetes**: Production deployment with secrets and health checks
- **Cloud Ready**: Environment variable configuration for various cloud providers

**Environment Variables:**
- `DATABASE_TYPE`: Database type toggle (`sqlite` or `mysql`) - defaults to `sqlite`
- `SQLITE_FILE`: SQLite database filename (when using SQLite) - defaults to `todos.db`
- `DATABASE_URL`: Full connection string (overrides DATABASE_TYPE and individual settings)
- `MYSQL_HOST/PORT/USER/PASSWORD/DATABASE`: Individual MySQL settings (when DATABASE_TYPE=mysql)
- `FLASK_ENV`: Environment mode (development/production)
- `PORT`: Application port (cloud deployment)
- `SPLUNK_HEC_URL`: Splunk HTTP Event Collector URL (optional)
- `SPLUNK_HEC_TOKEN`: Splunk HEC authentication token (optional)
- `SPLUNK_INDEX`: Splunk index name - defaults to `main`
- `SPLUNK_SOURCE`: Splunk source name - defaults to `todoapp`
- `SPLUNK_VERIFY_SSL`: SSL verification for Splunk - defaults to `true`

**Database Switching:**
```bash
# Use SQLite (default)
DATABASE_TYPE=sqlite

# Use MySQL
DATABASE_TYPE=mysql

# Use explicit connection string (overrides above)
DATABASE_URL=mysql+pymysql://user:pass@host:port/db
```

**Splunk Integration:**
```bash
# Configure Splunk HEC
SPLUNK_HEC_URL=https://your-splunk-instance.com:8088
SPLUNK_HEC_TOKEN=your-hec-token-here

# Optional Splunk settings
SPLUNK_INDEX=main
SPLUNK_SOURCE=todoapp
SPLUNK_VERIFY_SSL=true
```

**Splunk Features:**
- **Automatic request logging**: All HTTP requests logged to Splunk with duration, status, endpoint
- **Business event logging**: Todo creation, updates, deletions logged with context
- **Error logging**: Application errors with stack traces and context
- **Database operation logging**: Success/failure of database operations
- **Metrics export**: Export Prometheus metrics to Splunk HEC via `/splunk/export-metrics`
- **Connection testing**: Test Splunk connectivity via `/splunk/test`