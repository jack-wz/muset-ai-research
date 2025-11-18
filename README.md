# Muset AI - Intelligent Writing Assistant

An AI-powered writing assistant built with FastAPI, Next.js, LangChain, and Claude AI.

## Overview

Muset is an intelligent writing assistant that helps users create high-quality content with AI assistance. It features a rich text editor, real-time chat interface, file management, and advanced AI capabilities powered by Claude and DeepAgent architecture.

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **Cache**: Redis
- **ORM**: SQLAlchemy 2.0
- **AI**: LangChain + LangGraph + Anthropic Claude
- **Testing**: Pytest + Hypothesis

### Frontend
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + Emotion
- **UI Components**: Radix UI
- **Editor**: TipTap
- **State**: Zustand

## Project Structure

```
muset-ai-research/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Core configurations
│   │   ├── db/          # Database setup
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic
│   │   └── utils/       # Utilities
│   ├── tests/           # Backend tests
│   └── pyproject.toml   # Python dependencies
├── frontend/            # Next.js frontend
│   ├── app/            # Next.js pages
│   ├── components/     # React components
│   ├── lib/            # Utilities
│   └── package.json    # Node dependencies
├── muset-research/      # Research and design docs
│   └── analysis/       # Product analysis
├── .kiro/              # Project specifications
│   └── specs/
├── docker-compose.yml  # Docker services
└── .pre-commit-config.yaml  # Code quality hooks
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Poetry

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd muset-ai-research
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start database and Redis**
```bash
docker-compose up -d postgres redis
```

4. **Backend setup**
```bash
cd backend
poetry install
poetry shell
alembic upgrade head
uvicorn app.main:app --reload --port 7989
```

5. **Frontend setup**
```bash
cd frontend
npm install
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:7989
- API Docs: http://localhost:7989/docs

### Using Docker Compose

To run the entire stack with Docker:

```bash
docker-compose up -d
```

This will start:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Backend API (port 7989)
- Frontend (port 3000)

## Development

### Code Quality

Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

Format and lint:
```bash
# Backend
cd backend
black app tests
isort app tests
flake8 app tests

# Frontend
cd frontend
npm run format
npm run lint
```

### Testing

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## Documentation

- [Product Overview](./muset-research/analysis/01-产品概述.md)
- [UI Components](./muset-research/analysis/02-UI组件清单.md)
- [Interaction Flows](./muset-research/analysis/03-功能交互流程.md)
- [Design Specifications](./muset-research/analysis/04-视觉设计规范.md)
- [Technical Implementation](./muset-research/analysis/05-技术实现方案.md)
- [Data Models](./muset-research/analysis/06-数据模型设计.md)

## Features

- Rich text editor with AI assistance
- Real-time chat interface
- File management and version history
- Project and workspace management
- MCP (Model Context Protocol) integration
- Claude Skills support
- Multi-language support
- Writing style customization

## License

Proprietary
