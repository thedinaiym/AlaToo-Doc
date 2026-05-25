# alatoo-doc

Basic FastAPI project with asynchronous PostgreSQL access through SQLAlchemy and asyncpg.

## Setup

Create a `.env` file from `.env.example` and update `DATABASE_URL` for your local PostgreSQL database.

```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The health endpoint is available at `GET /health`.
