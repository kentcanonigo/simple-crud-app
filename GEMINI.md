# Gemini Code Assistant Guidance

This file provides guidance to the Gemini Code Assistant when working with code in this repository.

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

# Apply migration (run this from within the app pod in Kubernetes)
flask db upgrade
```

**Kubernetes deployment:**

```bash
# Apply all resources in the todo-app namespace
kubectl apply -f k8s-deployment.yaml
```

**Access points:**

- Web UI: http://localhost:5000 (or the LoadBalancer IP in Kubernetes)
- API endpoints: http://localhost:5000/api/todos
- Prometheus metrics: http://localhost:5000/metrics

## Architecture Overview

Production-ready Flask todo application with a MySQL backend, designed for Kubernetes.

**Core Components:**

- `app.py`: The main Flask application.
- `templates/index.html`: Bootstrap frontend with embedded JavaScript for API interaction.
- `k8s-deployment.yaml`: Contains all Kubernetes resources for deployment.

**Key Architecture Patterns:**

- **Environment-based configuration**: Database settings are injected via environment variables from Kubernetes Secrets.
- **Containerized Deployment**: Ready for production deployment with Docker and Kubernetes.
- **Stateful Database**: A `StatefulSet` is used to manage the MySQL database, ensuring stable storage and network identity.
- **REST API design**: `/api/todos` endpoints follow REST conventions.
- **Database Migrations**: `Flask-Migrate` is used for database schema versioning.
- **Structured Logging**: The application outputs structured JSON logs to `stdout`, suitable for collection by an observability platform (like a Splunk or OpenTelemetry collector).
- **Prometheus Metrics**: A `/metrics` endpoint is exposed for Prometheus to scrape request and latency metrics.

**Kubernetes Architecture:**

- **Namespace**: All resources are deployed in the `todo-app` namespace.
- **Application**: A `Deployment` manages the stateless Flask application pods.
- **Database**: A `StatefulSet` manages the MySQL pod, which uses a `PersistentVolumeClaim` to store data.
- **Configuration**: `Secrets` are used to manage the database URL and credentials.
- **Networking**: A `LoadBalancer` `Service` exposes the application, and a headless `Service` provides a stable DNS endpoint for the database.

**Data Flow:**

1. Frontend JavaScript makes AJAX calls to the `/api/todos` endpoints, exposed via a `LoadBalancer` `Service`.
2. The Flask application `Deployment` handles CRUD operations via SQLAlchemy.
3. The application connects to the MySQL `StatefulSet` using its internal `Service` name (`mysql-service.todo-app`).
4. All requests are logged as JSON to `stdout`.
5. Prometheus scrapes metrics from the `/metrics` endpoint of the application pods.

**Environment Variables:**

- `DATABASE_TYPE`: Can be set to `mysql` or `sqlite` for local development.
- `DATABASE_URL`: The full database connection string. In Kubernetes, this is injected from a `Secret`.
- `FLASK_ENV`: Set to `development` or `production`.
- `PORT`: The port the application listens on (defaults to 5000).
