# K-pop Database API

A production-style backend for K-pop idols, groups, albums, and songs, built with FastAPI, PostgreSQL, and Redis. The project focuses on doing the fundamentals properly: normalized relational schema, JWT auth with role-based access control, pagination/sorting/filtering, N+1-safe queries, and a Redis-backed rate limiter — rather than piling on features.

## Features

- **CRUD for four core resources**: Groups, Idols, Albums, Songs, with strict parent-must-exist-first creation (no nested/inline creation of child resources).
- **Auth**: JWT access + refresh tokens, password hashing (bcrypt), login/refresh/me endpoints.
- **RBAC**: Public read access on list endpoints, authenticated access on detail endpoints, admin-only on writes (create/update/delete). Enforced with a `require_role` dependency.
- **Pagination, sorting, filtering, search**: All list endpoints support `skip`/`limit`, an allow-listed `sort_by` + `order_by`, resource-specific filters, and case-insensitive partial-match search (`ILIKE`) across relevant text fields, including punctuation-normalized group name search (e.g. matching `(G)I-DLE` regardless of formatting).
- **N+1 query prevention**: All GET endpoints use `selectinload` to eager-load relationships instead of lazy-loading per row.
- **Rate limiting**: A custom Redis-based middleware (atomic `INCR`/`EXPIRE`) limiting each client to 10 requests per 60 seconds, safe across multiple worker processes.
- **Database migrations**: Alembic-managed schema, including a Postgres enum migration for gender.
- **Data seeding**: An idempotent seed script that loads idols and groups from a cleaned Kaggle dataset, with group-name casing collisions normalized before load.
- **Logging & error handling**: Request logging middleware plus a global exception handler that returns a consistent 500 response instead of leaking stack traces.
- **Tests**: Pytest suite covering albums, groups, idols, and songs.
- **Dockerized**: `docker-compose` spins up Postgres, Redis, and the API together.

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (via SQLAlchemy 2.0 ORM)
- **Migrations**: Alembic
- **Caching / Rate limiting**: Redis
- **Auth**: python-jose (JWT), passlib/bcrypt (password hashing)
- **Validation**: Pydantic v2 / pydantic-settings
- **Testing**: Pytest
- **Containerization**: Docker, Docker Compose

## Data Model

- `Group` — has many `Album`s and many `Idol`s (members).
- `Album` — belongs to a `Group` (nullable FK), has many `Song`s.
- `Song` — belongs to an `Album` (nullable FK).
- `Idol` — belongs to a `Group` (nullable FK).
- `User` — for auth, with a `role` (`user` / `admin`) used for RBAC.

Foreign keys use `ON DELETE SET NULL`, so deleting a group or album does not cascade-delete its members/tracks — it just detaches them. Indexes are added on all foreign keys and on commonly filtered/searched columns (e.g. idol stage name, country).

> Note: this is the v1 schema, intentionally kept simple. A v2 redesign is planned to introduce a base `Person` entity (so non-idols can also be song composers/lyricists), a `SongCredit` join table for multi-person/multi-role song credits, and a many-to-many song–group relationship to support collaboration tracks.

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/nmf-wasi/Kpop-DataBase.git
   cd Kpop-DataBase
   ```

2. Create a `.env` file in the project root with at least:
   ```
   SECRET_KEY=your-secret-key-here
   ```
   (`DATABASE_URL`, `TEST_DATABASE_URL`, and `REDIS_HOST` are already set for the Docker network in `docker-compose.yml`.)

3. Start the stack:
   ```bash
   docker-compose up --build
   ```
   This brings up Postgres, Redis, and the API.

4. Run migrations (inside the `api` container):
   ```bash
   docker-compose exec api alembic upgrade head
   ```

5. Seed the database:
   ```bash
   docker-compose exec api python -m app.scripts.seed
   ```

The API will be available at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

### Running Tests

```bash
docker-compose exec api pytest
```

## API Overview

All routes are prefixed with `/api`.

| Resource | Base path | Public | Auth required | Admin only |
|---|---|---|---|---|
| Users | `/api/users` | register, login, refresh | me, update, delete | role change |
| Idols | `/api/idols` | list | detail | create, update, delete |
| Groups | `/api/groups` | list | detail | create, update, delete |
| Albums | `/api/albums` | list | detail | create, update, delete |
| Songs | `/api/songs` | list | detail | create, update, delete |

Each list endpoint supports `skip`, `limit`, `sort_by`, `order_by`, `search`, and resource-specific filters (e.g. `country`, `group_id`).

## Project Structure

```
app/
├── config/       # settings and enums
├── core/         # logging setup
├── data/         # source CSV and processed seed data
├── database/     # SQLAlchemy engine/session setup
├── middleware/   # request logging, Redis rate limiter
├── models/       # SQLAlchemy models
├── routers/      # FastAPI route handlers per resource
├── schemas/      # Pydantic request/response schemas
├── scripts/      # seed script
├── security/     # password hashing, JWT token handling
├── src/          # FastAPI app entrypoint (main.py)
├── test/         # pytest test suite
└── utils/        # slug generation
alembic/          # migration environment and versions
docker-compose.yml
Dockerfile
```

## Roadmap

- LLM-integrated endpoint (`GET /idols/{id}/bio-summary`) calling the Anthropic API directly.
- v2 schema redesign: `Person` base entity, `SongCredit` join table, many-to-many song–group relationship for collaborations.
