# Enterprise FastAPI Core

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready, enterprise-grade REST API built with FastAPI, featuring clean architecture, comprehensive observability, robust security, and cloud-native deployment capabilities.

## 🚀 Features

- **Clean Architecture**: Domain-driven design with clear separation of concerns
- **Async Everything**: SQLAlchemy 2.0 async, Redis async, full async/await support
- **Type Safety**: Complete type hints with MyPy static type checking
- **Authentication**: JWT-based authentication with bcrypt password hashing
- **Caching**: Redis-based caching layer with configurable TTL
- **Background Tasks**: Celery task queue with Redis broker
- **Observability**: OpenTelemetry tracing, structured JSON logging, Prometheus metrics
- **Security**: Input validation, rate limiting, CORS, SQL injection prevention
- **Database Migrations**: Alembic for version-controlled schema changes
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Code Quality**: Ruff linting/formatting, MyPy type checking, pre-commit hooks
- **Containerization**: Docker and Docker Compose configurations
- **Kubernetes Ready**: Kustomize and Helm chart configurations
- **Development Tools**: Comprehensive Makefile, hot-reload, debugging support

## 📋 Table of Contents

- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Development](#-development)
- [Configuration](#-configuration)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)

## 🏗 Architecture

```
┌─────────────┐
│   Clients   │
└──────┬──────┘
       │
┌──────▼──────────────────────────────────────┐
│          Load Balancer/Ingress              │
└──────┬──────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│         FastAPI Application Layer           │
│  ┌────────────────────────────────────┐    │
│  │  API Routes (v1, v2, ...)          │    │
│  ├────────────────────────────────────┤    │
│  │  Middleware (CORS, Rate Limit,     │    │
│  │  Logging, Tracing)                 │    │
│  ├────────────────────────────────────┤    │
│  │  Services (Business Logic)         │    │
│  ├────────────────────────────────────┤    │
│  │  Repositories (Data Access)        │    │
│  └────────────────────────────────────┘    │
└──────┬──────────────────┬───────────────────┘
       │                  │
┌──────▼──────┐    ┌──────▼──────────┐
│  PostgreSQL │    │  Redis Cache    │
│  Database   │    │  & Message      │
│             │    │  Broker         │
└─────────────┘    └──────┬──────────┘
                          │
                   ┌──────▼──────────┐
                   │ Celery Workers  │
                   │ & Beat Scheduler│
                   └─────────────────┘
```

### Layer Architecture

- **API Layer** (`app/api/`): FastAPI routers, request/response handling
- **Service Layer** (`app/services/`): Business logic and use cases
- **Repository Layer** (`app/repositories/`): Data access abstraction
- **Model Layer** (`app/models/`): SQLAlchemy ORM models
- **Schema Layer** (`app/schemas/`): Pydantic validation models
- **Core Layer** (`app/core/`): Configuration, security, database setup
- **Middleware Layer** (`app/middlewares/`): Cross-cutting concerns

## 📦 Prerequisites

- **Python**: 3.11 or higher
- **UV**: Fast Python package manager ([installation guide](https://docs.astral.sh/uv/))
- **PostgreSQL**: 14 or higher
- **Redis**: 6 or higher
- **Docker** (optional): For containerized development
- **Kubernetes** (optional): For production deployment

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/enterprise-fastapi-core.git
cd enterprise-fastapi-core
```

### 2. Install Dependencies

```bash
# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
make install
```

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and update the following critical values:
# - SECRET_KEY: Generate with `openssl rand -hex 32`
# - DATABASE_URL: Your PostgreSQL connection string
# - REDIS_URL: Your Redis connection string
```

### 4. Start Services with Docker Compose

```bash
# Start all services (PostgreSQL, Redis, API, Celery)
make docker-up

# The API will be available at http://localhost:8000
```

### 5. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Alternative: Local Development (Without Docker)

```bash
# Ensure PostgreSQL and Redis are running locally

# Run database migrations
make migrate

# Create a superuser (optional)
uv run python scripts/create_superuser.py

# Start the development server
make dev

# In separate terminals, start Celery worker and beat
make worker
make beat
```

## 💻 Development

### Available Make Commands

```bash
make help              # Show all available commands
make install           # Install dependencies with UV
make format            # Format code with Ruff
make lint              # Lint code with Ruff
make typecheck         # Type check with MyPy
make test              # Run tests with pytest
make test-cov          # Run tests with coverage report
make migrate           # Run database migrations
make migrate-create    # Create new migration (use MSG='description')
make dev               # Run development server with hot-reload
make worker            # Run Celery worker
make beat              # Run Celery beat scheduler
make docker-build      # Build Docker image
make docker-up         # Start Docker Compose services
make docker-down       # Stop Docker Compose services
make clean             # Clean up cache and temporary files
```

### Code Quality Tools

```bash
# Format code
make format

# Run linter
make lint

# Type checking
make typecheck

# Run all quality checks
make format lint typecheck
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run hooks manually
uv run pre-commit run --all-files
```

### Database Migrations

```bash
# Create a new migration
make migrate-create MSG="add user table"

# Apply migrations
make migrate

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history
```

### Creating a Superuser

```bash
# Interactive superuser creation
uv run python scripts/create_superuser.py

# Or with Docker
docker-compose exec api python scripts/create_superuser.py
```

## ⚙️ Configuration

### Environment Variables

All configuration is managed through environment variables. See `.env.example` for a complete list.

#### Application Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | `Enterprise FastAPI` |
| `DEBUG` | Enable debug mode | `false` |
| `ENVIRONMENT` | Environment (development/staging/production) | `development` |
| `API_V1_PREFIX` | API v1 URL prefix | `/api/v1` |

#### Database Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql+asyncpg://postgres:postgres@localhost:5432/enterprise_api` |
| `DB_POOL_SIZE` | Connection pool size | `20` |
| `DB_MAX_OVERFLOW` | Max overflow connections | `10` |
| `DB_POOL_TIMEOUT` | Pool timeout in seconds | `30` |
| `DB_POOL_RECYCLE` | Connection recycle time | `3600` |

#### Redis Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `REDIS_POOL_SIZE` | Redis connection pool size | `10` |
| `CACHE_TTL` | Default cache TTL in seconds | `3600` |
| `SESSION_TTL` | Session TTL in seconds | `86400` |

#### JWT Authentication Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT secret key (⚠️ CHANGE IN PRODUCTION) | - |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiration | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiration | `7` |
| `BCRYPT_COST_FACTOR` | Bcrypt hashing cost | `12` |

#### CORS Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ORIGINS` | Allowed origins (JSON array) | `["http://localhost:3000"]` |
| `CORS_ALLOW_CREDENTIALS` | Allow credentials | `true` |
| `CORS_ALLOW_METHODS` | Allowed HTTP methods | `["GET","POST","PUT","PATCH","DELETE"]` |

#### Rate Limiting Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `RATE_LIMIT_ENABLED` | Enable rate limiting | `true` |
| `RATE_LIMIT_PER_MINUTE` | Requests per minute | `60` |
| `RATE_LIMIT_PER_HOUR` | Requests per hour | `1000` |

#### OpenTelemetry Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `OTEL_ENABLED` | Enable OpenTelemetry | `true` |
| `OTEL_SERVICE_NAME` | Service name for traces | `enterprise-api` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint | `http://localhost:4317` |
| `OTEL_TRACES_SAMPLER` | Trace sampling strategy | `always_on` |

#### Logging Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Log format (json/text) | `json` |

#### API Documentation Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `DOCS_ENABLED` | Enable API documentation | `true` |
| `DOCS_URL` | Swagger UI path | `/docs` |
| `REDOC_URL` | ReDoc path | `/redoc` |
| `OPENAPI_URL` | OpenAPI JSON path | `/openapi.json` |

### Generating a Secret Key

```bash
# Generate a secure secret key
openssl rand -hex 32
```

## 📚 API Documentation

### Interactive Documentation

Once the application is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
  - Interactive API explorer
  - Try out endpoints directly
  - View request/response schemas

- **ReDoc**: http://localhost:8000/redoc
  - Clean, readable documentation
  - Better for sharing with stakeholders

### API Endpoints

#### Health Checks

```
GET /health/live   - Liveness probe (application running)
GET /health/ready  - Readiness probe (dependencies available)
```

#### Authentication

```
POST /api/v1/auth/register  - Register new user
POST /api/v1/auth/login     - Login and get JWT tokens
POST /api/v1/auth/refresh   - Refresh access token
```

#### User Management

```
GET    /api/v1/users        - List users (paginated)
POST   /api/v1/users        - Create user
GET    /api/v1/users/{id}   - Get user by ID
PUT    /api/v1/users/{id}   - Update user
DELETE /api/v1/users/{id}   - Delete user
GET    /api/v1/users/me     - Get current user
```

#### Background Tasks

```
POST /api/v1/tasks/send-email  - Trigger email task
GET  /api/v1/tasks/{task_id}   - Get task status
```

#### Metrics

```
GET /metrics  - Prometheus metrics endpoint
```

### Authentication Flow

1. **Register**: `POST /api/v1/auth/register`
   ```json
   {
     "email": "user@example.com",
     "password": "SecurePassword123!",
     "full_name": "John Doe"
   }
   ```

2. **Login**: `POST /api/v1/auth/login`
   ```json
   {
     "username": "user@example.com",
     "password": "SecurePassword123!"
   }
   ```
   Response:
   ```json
   {
     "access_token": "eyJ...",
     "refresh_token": "eyJ...",
     "token_type": "bearer"
   }
   ```

3. **Use Token**: Include in Authorization header
   ```
   Authorization: Bearer eyJ...
   ```

4. **Refresh Token**: `POST /api/v1/auth/refresh`
   ```json
   {
     "refresh_token": "eyJ..."
   }
   ```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
make test

# Run with coverage report
make test-cov

# Run specific test file
uv run pytest tests/unit/test_services.py -v

# Run tests by marker
uv run pytest -m unit
uv run pytest -m integration
```

### Test Structure

```
tests/
├── unit/           # Unit tests (isolated, fast)
├── integration/    # Integration tests (database, redis)
└── api/            # API endpoint tests
```

### Writing Tests

```python
import pytest
from httpx import AsyncClient
from app.cmd.main import app

@pytest.mark.asyncio
async def test_create_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/users",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 201
```

## 🚢 Deployment

### Docker Deployment

```bash
# Build image
make docker-build

# Run with Docker Compose
make docker-up

# View logs
docker-compose logs -f api

# Stop services
make docker-down
```

### Kubernetes Deployment

#### Using Kustomize

```bash
# Deploy to development
kubectl apply -k k8s/overlays/development

# Deploy to production
kubectl apply -k k8s/overlays/production

# View resources
kubectl get all -n enterprise-api
```

#### Using Helm

```bash
# Install chart
helm install enterprise-api ./helm/enterprise-api \
  -f helm/enterprise-api/values-prod.yaml \
  --namespace enterprise-api \
  --create-namespace

# Upgrade release
helm upgrade enterprise-api ./helm/enterprise-api \
  -f helm/enterprise-api/values-prod.yaml

# Uninstall
helm uninstall enterprise-api -n enterprise-api
```

### Environment-Specific Configurations

- **Development**: `k8s/overlays/development/` or `helm/enterprise-api/values-dev.yaml`
- **Staging**: `k8s/overlays/staging/`
- **Production**: `k8s/overlays/production/` or `helm/enterprise-api/values-prod.yaml`

### Health Checks

Kubernetes health checks are configured for:
- **Liveness**: `/health/live` - Restarts pod if failing
- **Readiness**: `/health/ready` - Removes from load balancer if failing

### Scaling

```bash
# Manual scaling
kubectl scale deployment enterprise-api --replicas=5

# Horizontal Pod Autoscaler (HPA) is configured in Helm chart
# Scales based on CPU/memory usage
```

### Monitoring

The application exposes Prometheus metrics at `/metrics`:
- Request duration and count
- Active connections
- Cache hit/miss rates
- Custom business metrics

Configure Prometheus to scrape the `/metrics` endpoint or use the ServiceMonitor resource (included in Helm chart).

## 📁 Project Structure

```
enterprise-fastapi-core/
├── alembic/                    # Database migrations
│   ├── versions/              # Migration scripts
│   ├── env.py                 # Alembic environment
│   └── script.py.mako         # Migration template
├── app/                        # Application code
│   ├── api/                   # API routes
│   │   └── v1/               # API version 1
│   │       ├── auth.py       # Authentication endpoints
│   │       ├── health.py     # Health check endpoints
│   │       ├── tasks.py      # Task endpoints
│   │       └── users.py      # User endpoints
│   ├── cmd/                   # Application entrypoints
│   │   └── main.py           # FastAPI app initialization
│   ├── core/                  # Core functionality
│   │   ├── database.py       # Database configuration
│   │   ├── exceptions.py     # Custom exceptions
│   │   ├── metrics.py        # Prometheus metrics
│   │   ├── security.py       # Security utilities
│   │   ├── settings.py       # Application settings
│   │   └── telemetry.py      # OpenTelemetry setup
│   ├── dependencies/          # Dependency injection
│   │   ├── auth.py           # Auth dependencies
│   │   ├── cache.py          # Cache dependencies
│   │   └── database.py       # Database dependencies
│   ├── middlewares/           # Middleware components
│   │   ├── cors.py           # CORS middleware
│   │   ├── logging.py        # Logging middleware
│   │   ├── rate_limit.py     # Rate limiting
│   │   └── tracing.py        # Tracing middleware
│   ├── models/                # SQLAlchemy models
│   │   ├── base.py           # Base model
│   │   └── user.py           # User model
│   ├── repositories/          # Data access layer
│   │   ├── base.py           # Base repository
│   │   └── user.py           # User repository
│   ├── schemas/               # Pydantic schemas
│   │   ├── auth.py           # Auth schemas
│   │   ├── health.py         # Health schemas
│   │   ├── task.py           # Task schemas
│   │   └── user.py           # User schemas
│   ├── services/              # Business logic
│   │   ├── auth.py           # Auth service
│   │   ├── cache.py          # Cache service
│   │   └── user.py           # User service
│   └── tasks/                 # Background tasks
│       ├── celery_app.py     # Celery configuration
│       └── email.py          # Email tasks
├── helm/                       # Helm charts
│   └── enterprise-api/        # Main chart
│       ├── templates/         # Kubernetes manifests
│       └── values.yaml        # Default values
├── k8s/                        # Kubernetes configs
│   ├── base/                  # Base Kustomize config
│   └── overlays/              # Environment overlays
├── scripts/                    # Utility scripts
│   ├── create_superuser.py   # Create admin user
│   └── init_db.py            # Initialize database
├── tests/                      # Test suite
│   ├── api/                   # API tests
│   ├── integration/           # Integration tests
│   └── unit/                  # Unit tests
├── .env.example               # Example environment file
├── .pre-commit-config.yaml    # Pre-commit hooks
├── alembic.ini                # Alembic configuration
├── docker-compose.yml         # Docker Compose config
├── Dockerfile                 # Docker image definition
├── Makefile                   # Development commands
├── pyproject.toml             # Project dependencies
└── README.md                  # This file
```

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Run quality checks**: `make format lint typecheck test`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Write docstrings for public APIs
- Keep functions small and focused
- Write tests for new features

### Commit Messages

Follow conventional commits format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Build/tooling changes

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - SQL toolkit and ORM
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [Celery](https://docs.celeryq.dev/) - Distributed task queue
- [OpenTelemetry](https://opentelemetry.io/) - Observability framework
- [UV](https://docs.astral.sh/uv/) - Fast Python package manager

## 📞 Support

- **Documentation**: [Link to your docs]
- **Issues**: [GitHub Issues](https://github.com/yourusername/enterprise-fastapi-core/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/enterprise-fastapi-core/discussions)

---

**Built with ❤️ using FastAPI and modern Python tooling**
