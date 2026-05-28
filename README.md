# alatoo-doc

Basic FastAPI project with asynchronous PostgreSQL access through SQLAlchemy and asyncpg.

## Setup

Create a `.env` file from `.env.example` and update `DATABASE_URL` for your local PostgreSQL database.

```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```
<img width="2851" height="1624" alt="Снимок экрана 2026-05-28 151611" src="https://github.com/user-attachments/assets/92b7d50e-0604-4f3f-9dff-69b54995300d" />
<img width="2879" height="1630" alt="Снимок экрана 2026-05-28 160312" src="https://github.com/user-attachments/assets/2b1898c6-c9ab-4bd3-ae6f-27782529ee04" />
<img width="2879" height="1635" alt="Снимок экрана 2026-05-28 160357" src="https://github.com/user-attachments/assets/46290681-b3dc-40e8-9c84-fbb7402aa951" />

The health endpoint is available at `GET /health`.
