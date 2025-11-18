# Muset Backend

AI Writing Assistant Backend powered by FastAPI and LangChain.

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (via Docker)
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **AI Framework**: LangChain + LangGraph
- **Task Queue**: Redis
- **Testing**: Pytest + Hypothesis

## Getting Started

### Prerequisites

- Python 3.11+
- Poetry
- Docker & Docker Compose

### Installation

1. Install dependencies:
```bash
poetry install
```

2. Activate virtual environment:
```bash
poetry shell
```

3. Copy environment variables:
```bash
cp ../.env.example .env
```

4. Start database and Redis:
```bash
docker-compose up -d
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start development server:
```bash
uvicorn app.main:app --reload --port 7989
```

## Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Core configurations
│   ├── db/               # Database setup
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── utils/            # Utilities
├── tests/                # Test files
├── alembic/              # Database migrations
├── pyproject.toml        # Poetry configuration
└── README.md
```

## Development

### Code Quality

Format code:
```bash
black app tests
isort app tests
```

Run linter:
```bash
flake8 app tests
mypy app
```

### Testing

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

Run property-based tests:
```bash
pytest -m property
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:7989/docs
- ReDoc: http://localhost:7989/redoc
