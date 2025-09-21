# Simple Todo List App

A production-ready Flask todo list application with a Bootstrap 5 frontend, MySQL/SQLite database support, Prometheus metrics, and structured JSON logging.

## 🚀 Features

- ✅ **Full CRUD Operations** - Create, read, update, and delete todos.
- ✅ **Responsive UI** - Interactive frontend built with Bootstrap 5 and vanilla JavaScript.
- ✅ **Database Flexibility** - Toggle between SQLite and MySQL with environment variables.
- ✅ **Production Ready** - Docker and Kubernetes support for easy deployment.
- ✅ **Observability** - Prometheus metrics endpoint and structured JSON logging.
- ✅ **Database Migrations** - Flask-Migrate support for schema versioning.
- ✅ **Testing Panel** - UI for health checks and simulating various errors (404, 500, timeout, etc.).

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

## 🌐 Access Points

- **Web UI**: http://localhost:5000
- **API**: http://localhost:5000/api/todos
- **Prometheus Metrics**: http://localhost:5000/metrics
- **Health Check**: http://localhost:5000/health

## 📊 API Endpoints

### Todo Operations

- `GET /api/todos` - List all todos
- `POST /api/todos` - Create new todo
- `PUT /api/todos/<id>` - Update todo
- `DELETE /api/todos/<id>` - Delete todo

### Monitoring & Health

- `GET /metrics` - Prometheus metrics
- `GET /health` - Application health check

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

## 📦 Deployment

### Kubernetes

The Kubernetes manifests are located in the `k8s/` directory.

```bash
# Apply all manifests
kubectl apply -f k8s/
```

Make sure your Kubernetes cluster has access to the Docker image. The Jenkinsfile provides an example of how to build and push the image, and then deploy to Kubernetes.

### Docker

```bash
# Build and run
docker build -t todoapp .
docker run -p 5000:5000 todoapp
```

## 🔍 Monitoring Features

### Prometheus Metrics

- HTTP request counts by method and endpoint.
- Request latency histograms.

### Structured Logging

The application outputs structured JSON logs to `stdout`. This is ideal for collection and analysis by a log aggregation platform like Elasticsearch, Splunk, or Datadog.

- **Request Logging**: All HTTP requests with duration and status.
- **Business Events**: Todo operations (create, update, delete) with context.
- **Error Logging**: Application errors and database operation failures.

## 🏗️ Architecture

- **Backend**: Flask with SQLAlchemy ORM
- **Frontend**: Bootstrap 5 with vanilla JavaScript
- **Database**: SQLite (development) / MySQL (production)
- **Monitoring**: Prometheus for metrics and structured JSON logging.
- **Deployment**: Docker, Kubernetes, cloud-ready.

## 🧪 Testing

The web UI includes a "Testing & Monitoring" panel to perform health checks and simulate various error conditions.

You can also use `curl` to test the API endpoints:

```bash
# Test API
curl http://localhost:5000/api/todos

# Create todo
curl -X POST http://localhost:5000/api/todos \
  -H "Content-Type: application/json" \
  -d '''{"title": "Test Todo", "description": "Testing the API"}'''

# Check metrics
curl http://localhost:5000/metrics

# Check health
curl http://localhost:5000/health
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

- Use `FLASK_ENV=production`.
- Configure an external MySQL database.
- Set up a log collector to process the structured JSON logs from `stdout`.
- Use proper secrets management for database credentials in Kubernetes.
- Deploy with multiple replicas for high availability.
- Configure a load balancer and SSL termination.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
