# Simple Todo List App

A production-ready Flask todo list application with Bootstrap frontend, MySQL/SQLite database support, Prometheus metrics, and Splunk integration.

## 🚀 Features

- ✅ **Full CRUD Operations** - Create, read, update, and delete todos
- ✅ **Responsive UI** - Bootstrap 5 frontend with interactive JavaScript
- ✅ **Database Flexibility** - Toggle between SQLite and MySQL with environment variables
- ✅ **Production Ready** - Docker, Kubernetes, and cloud deployment support
- ✅ **Metrics & Monitoring** - Prometheus metrics endpoint
- ✅ **Splunk Integration** - Comprehensive logging and metrics export to Splunk
- ✅ **Database Migrations** - Flask-Migrate support for schema versioning

## 🛠️ Quick Start

### Option 1: Docker Compose (Recommended)
```bash
# Clone and start the full stack
git clone <repository>
cd simple-crud-app
docker-compose up -d
```

### Option 2: Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment (copy and edit)
cp .env.example .env

# Run the application
python app.py
```

### Option 3: Local with MySQL
```bash
# Install and start MySQL
# Create database: CREATE DATABASE todoapp;
# Create user: CREATE USER 'todoapp'@'localhost' IDENTIFIED BY 'todoapp123';
# Grant permissions: GRANT ALL PRIVILEGES ON todoapp.* TO 'todoapp'@'localhost';

# Configure environment
echo "DATABASE_TYPE=mysql" >> .env

# Run application
python app.py
```

## 🌐 Access Points

- **Web UI**: http://localhost:5000
- **API**: http://localhost:5000/api/todos
- **Prometheus Metrics**: http://localhost:5000/metrics
- **Splunk Status**: http://localhost:5000/splunk/status

## 📊 API Endpoints

### Todo Operations
- `GET /api/todos` - List all todos
- `POST /api/todos` - Create new todo
- `PUT /api/todos/<id>` - Update todo
- `DELETE /api/todos/<id>` - Delete todo

### Monitoring & Observability
- `GET /metrics` - Prometheus metrics
- `GET /splunk/status` - Splunk integration status
- `POST /splunk/export-metrics` - Export metrics to Splunk
- `POST /splunk/test` - Test Splunk connection

## ⚙️ Configuration

### Database Configuration
```bash
# Use SQLite (default)
DATABASE_TYPE=sqlite
SQLITE_FILE=todos.db

# Use MySQL
DATABASE_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_USER=todoapp
MYSQL_PASSWORD=todoapp123
MYSQL_DATABASE=todoapp

# Use connection string (overrides above)
DATABASE_URL=mysql+pymysql://user:pass@host:port/database
```

### Splunk Integration (Optional)
```bash
SPLUNK_HEC_URL=https://your-splunk-instance.com:8088
SPLUNK_HEC_TOKEN=your-hec-token-here
SPLUNK_INDEX=main
SPLUNK_SOURCE=todoapp
```

## 📦 Deployment

### Kubernetes
```bash
# Update secrets in k8s-deployment.yaml
kubectl apply -f k8s-deployment.yaml
```

### Docker
```bash
# Build and run
docker build -t todoapp .
docker run -p 5000:5000 todoapp
```

## 🔍 Monitoring Features

### Prometheus Metrics
- HTTP request counts by method and endpoint
- Request latency histograms
- Python runtime metrics

### Splunk Logging
- **Request Logging**: All HTTP requests with duration and status
- **Business Events**: Todo operations with context
- **Error Logging**: Application errors with stack traces
- **Database Operations**: Success/failure of database operations

## 🏗️ Architecture

- **Backend**: Flask with SQLAlchemy ORM
- **Frontend**: Bootstrap 5 with vanilla JavaScript
- **Database**: SQLite (development) / MySQL (production)
- **Monitoring**: Prometheus + Splunk integration
- **Deployment**: Docker, Kubernetes, cloud-ready

## 🧪 Testing

```bash
# Test API
curl http://localhost:5000/api/todos

# Create todo
curl -X POST http://localhost:5000/api/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Todo", "description": "Testing the API"}'

# Check metrics
curl http://localhost:5000/metrics

# Check Splunk status
curl http://localhost:5000/splunk/status
```

## 📝 Development

### Database Migrations
```bash
# Initialize migrations (first time)
flask db init

# Create migration
flask db migrate -m "Add new field"

# Apply migration
flask db upgrade
```

### Environment Variables
See `.env.example` for all available configuration options.

## 🚀 Production Considerations

- Use `FLASK_ENV=production`
- Configure external MySQL database
- Set up Splunk HEC for logging
- Use proper secrets management for database credentials
- Deploy with multiple replicas for high availability
- Configure load balancer and SSL termination

## 📄 License

This project is open source and available under the [MIT License](LICENSE).