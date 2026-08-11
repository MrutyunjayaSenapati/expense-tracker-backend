# Expense Tracker FastAPI Backend

Production-grade FastAPI backend for the Expense Tracker application.

## Tech Stack
- **Framework:** FastAPI
- **Database / ORM:** PostgreSQL / SQLite with SQLAlchemy 2.x (Async)
- **Migrations:** Alembic
- **Auth:** Argon2id Password Hashing + JWT Access Tokens & Refresh Tokens
- **Testing:** Pytest + HTTPX AsyncClient

## Getting Started

### 1. Setup Virtual Environment
```bash
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Database Migrations
```bash
alembic upgrade head
```

### 4. Start the Backend Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Interactive API Documentation
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Schema:** [http://localhost:8000/api/v1/openapi.json](http://localhost:8000/api/v1/openapi.json)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

## Running Tests
```bash
python -m pytest tests -v
```

## Docker Support
```bash
docker-compose up --build
```
