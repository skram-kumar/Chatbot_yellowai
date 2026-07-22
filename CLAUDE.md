# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A minimal chatbot platform (assignment project). Users register/log in, create
projects ("agents"), attach prompts to a project, and chat with that agent
through an endpoint that forwards to OpenRouter's completion API for the LLM
response. The frontend is plain HTML/CSS/JS, served as static files
independent of the API (no frontend build tooling, no SSR).

This repo is greenfield — no code has been scaffolded yet. The sections below
describe the architecture and conventions to follow while building it out, not
things that already exist on disk. Update this file as real structure lands
so it stays accurate.

## Tech stack

- **FastAPI** — API framework, async endpoints for anything I/O-bound (DB, OpenRouter calls)
- **PostgreSQL** — primary datastore
- **SQLAlchemy** (async) — ORM
- **Alembic** — schema migrations
- **Pydantic / pydantic-settings** — request/response schemas and typed settings loaded from env vars
- **passlib[bcrypt]** — password hashing
- **python-jose** (or **pyjwt**) — JWT creation/verification
- **httpx** — async HTTP client for calling the OpenRouter API
- **uvicorn** — ASGI server
- **pytest** + **httpx.AsyncClient** / **pytest-asyncio** — tests

## Intended architecture

Layered by responsibility, not by feature, so auth/db/external-API concerns
stay swappable:

```
app/
  main.py            # FastAPI app factory, router registration, middleware
  core/
    config.py        # Settings (pydantic-settings), reads from environment/.env
    security.py       # password hashing, JWT encode/decode, current-user dependency
  db/
    session.py         # async engine + session factory
    base.py             # declarative base, shared mixins (id, timestamps)
  models/               # SQLAlchemy ORM models: User, Project, Prompt
  schemas/              # Pydantic request/response models, one module per resource
  api/
    routes/
      auth.py           # register, login
      projects.py       # CRUD for projects/agents + their prompts
      chat.py           # chat endpoint
    deps.py             # shared FastAPI dependencies (get_db, get_current_user)
  services/
    openrouter.py       # OpenRouter client: builds request, calls completion API, maps errors
  alembic/                # migration environment + versions
tests/
```

### Data model (as implied by requirements)

- `User` 1—N `Project` (a project belongs to exactly one user)
- `Project` 1—N `Prompt` (prompts are scoped to a project/agent)
- Chat endpoint: given a `project_id` and a user message, loads the project's
  prompt(s) as context, calls `services/openrouter.py`, returns the
  completion. Keep chat stateless unless/until conversation history is
  explicitly required.

### Request flow

Router (`api/routes/*`) → validates via Pydantic schema → dependency injects
DB session + current user (`api/deps.py`) → business logic lives in
`services/` or directly in the route for simple CRUD → SQLAlchemy model →
Postgres. External calls (OpenRouter) are isolated in `services/openrouter.py`
so the provider can be swapped without touching route code.

## Coding conventions

- **Naming**: descriptive, unabbreviated names for models, schemas, and
  functions (`ProjectCreate`, `get_current_user`, not `PC`, `gcu`). Pydantic
  schema classes follow `<Resource><Action>` (e.g. `UserRegister`,
  `ProjectRead`, `PromptUpdate`).
- **Modularity**: one router per resource under `api/routes/`; one model
  module per table under `models/`; no business logic in `main.py` beyond
  wiring. Keep the OpenRouter integration behind `services/openrouter.py` —
  routes should never call an LLM API directly.
- **Secrets & config**: all secrets (DB URL, JWT signing key, OpenRouter API
  key) come from environment variables via `core/config.py`
  (pydantic-settings), loaded from a local `.env` that is never committed.
  Never hardcode credentials, keys, or connection strings in source.
- **Auth**: hash passwords with bcrypt via passlib — never store or log plain
  passwords. JWTs are short-lived access tokens signed with a secret from
  env; verify signature and expiry on every protected route via a shared
  `get_current_user` dependency. Every project/prompt/chat route must confirm
  the resource belongs to the requesting user (no cross-user access by
  guessing IDs).
- **Error handling**: raise `HTTPException` with accurate status codes
  (400/401/403/404/422/502 for upstream OpenRouter failures) and consistent
  JSON error bodies; don't leak stack traces or upstream provider internals
  to the client. Wrap OpenRouter calls so network/timeout/rate-limit errors
  surface as clean 502/503s instead of unhandled exceptions.
- **Async**: DB and outbound HTTP calls are `async def` using the async
  SQLAlchemy session and `httpx.AsyncClient`.
- **Migrations**: schema changes go through Alembic migrations, not manual
  DDL or `create_all` in production paths.

## Commands

Not yet runnable — no `requirements.txt`/`pyproject.toml` or app code exists.
Once scaffolded, the expected commands are:

```bash
pip install -r requirements.txt          # or: poetry install / uv sync
uvicorn app.main:app --reload            # run the API locally
alembic upgrade head                     # apply migrations
alembic revision --autogenerate -m "..."  # create a migration after model changes
pytest                                    # run tests
pytest tests/test_auth.py::test_login     # run a single test
```
