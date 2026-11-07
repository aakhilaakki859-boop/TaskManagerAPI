# Task Manager API

A REST backend built with **FastAPI**, **SQLAlchemy 2.0** and **JWT authentication**.
Users register, log in, and manage their own private tasks.

## Features
- JWT auth (register / login), passwords hashed with bcrypt
- Task CRUD scoped to the logged-in user (no access to other users' data)
- Filtering by status and priority, pagination with `limit` / `offset`
- Pydantic validation, proper HTTP status codes
- Config via environment variables, pytest test suite with an in-memory DB

## Tech stack
Python 3.10+, FastAPI, SQLAlchemy, SQLite (swappable via `DATABASE_URL`), PyJWT, pytest

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # set a real SECRET_KEY
uvicorn app.main:app --reload
```
Interactive docs: http://127.0.0.1:8000/docs

## Run tests
```bash
pytest -v
```

## Endpoints
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /auth/register | no | Create account |
| POST | /auth/login | no | Get JWT (form data) |
| POST | /tasks | yes | Create task |
| GET | /tasks?status=&priority=&limit=&offset= | yes | List own tasks |
| GET | /tasks/{id} | yes | Get one task |
| PATCH | /tasks/{id} | yes | Partial update |
| DELETE | /tasks/{id} | yes | Delete task |
| GET | /health | no | Health check |

## Project structure
```
app/
  main.py        # app + router wiring
  config.py      # settings from env
  database.py    # engine, session, Base
  models.py      # User, Task
  schemas.py     # Pydantic request/response models
  security.py    # hashing + JWT
  deps.py        # get_current_user dependency
  routers/       # auth.py, tasks.py
tests/
```

## Design decisions
- A task from another user returns **404**, not 403, so task IDs can't be probed.
- `PATCH` uses `exclude_unset=True` so only the fields sent are changed.
- DB session is a per-request dependency, overridden in tests.