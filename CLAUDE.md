# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A minimal chatbot platform (assignment project). Users register/log in, create
projects ("agents"), attach prompts to a project, and chat with that agent
through an endpoint that forwards to Groq's OpenAI-compatible chat completions
API for the LLM response. The frontend is plain HTML/CSS/JS, served as static
files independent of the API (no frontend build tooling, no SSR).

Auth, project/prompt CRUD, and the chat endpoint are implemented (see
`app/`). The database is a hosted Neon Postgres instance, migrated via
Alembic. Update this file as the architecture evolves so it stays accurate.

## Tech stack

- **FastAPI** — API framework, async endpoints for anything I/O-bound (DB, Groq calls)
- **PostgreSQL** (Neon, hosted) — primary datastore
- **SQLAlchemy** (async, via `asyncpg`) — ORM
- **Alembic** — schema migrations
- **Pydantic / pydantic-settings** — request/response schemas and typed settings loaded from env vars
- **bcrypt** (direct, not passlib) — password hashing; passlib was dropped after its bug-detection
  routine crashed against modern bcrypt (>=4.x) — see `app/core/security.py`
- **python-jose** — JWT creation/verification
- **httpx** — async HTTP client for calling the Groq API
- **uvicorn** — ASGI server
- **pytest** + **httpx.AsyncClient** / **pytest-asyncio** — tests (not yet written)

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
      projects.py       # CRUD for projects/agents
      prompts.py        # CRUD for prompts, nested under /projects/{project_id}/prompts
      chat.py           # POST/GET /projects/{project_id}/chat
    deps.py             # shared FastAPI dependencies: get_db, get_current_user, get_owned_project
  services/
    llm.py              # Groq client: builds request, calls chat completions, maps errors
  alembic/                # migration environment + versions
tests/
```

### Data model

- `User` 1—N `Project` (a project belongs to exactly one user)
- `Project` 1—N `Prompt` (prompts are scoped to a project/agent; a project can
  have several — the chat endpoint uses the most recently created one as the
  active system prompt)
- `Project` 1—N `Message` (`role` is `user`/`assistant`; chat history is
  persisted per project, not stateless)
- Chat endpoint: given a `project_id` and a user message, saves the user
  message, builds the conversation (active prompt as system message + prior
  `Message` history + the new message), calls `services/llm.py`, saves and
  returns the assistant reply alongside the user message.

### Request flow

Router (`api/routes/*`) → validates via Pydantic schema → dependency injects
DB session + current user (`api/deps.py`) → ownership on project-scoped
routes is enforced via the shared `get_owned_project` dependency (404s,
never 403, if the project doesn't exist or isn't the caller's — the two
cases are indistinguishable in the response) → business logic lives in
`services/` or directly in the route for simple CRUD → SQLAlchemy model →
Postgres. External calls (Groq) are isolated in `services/llm.py` so the
provider can be swapped without touching route code; failures there are
caught and surfaced as a clean `502`, never an unhandled `500`.

## Coding conventions

- **Naming**: descriptive, unabbreviated names for models, schemas, and
  functions (`ProjectCreate`, `get_current_user`, not `PC`, `gcu`). Pydantic
  schema classes follow `<Resource><Action>` (e.g. `UserRegister`,
  `ProjectRead`, `PromptUpdate`).
- **Modularity**: one router per resource under `api/routes/`; one model
  module per table under `models/`; no business logic in `main.py` beyond
  wiring. Keep the Groq integration behind `services/llm.py` — routes should
  never call an LLM API directly.
- **Secrets & config**: all secrets (DB URL, JWT signing key, Groq API key)
  come from environment variables via `core/config.py` (pydantic-settings),
  loaded from a local `.env` that is never committed. Never hardcode
  credentials, keys, or connection strings in source.
- **Auth**: hash passwords with bcrypt — never store or log plain passwords.
  JWTs are short-lived access tokens signed with a secret from env; verify
  signature and expiry on every protected route via a shared
  `get_current_user` dependency. Every project/prompt/chat route must confirm
  the resource belongs to the requesting user via `get_owned_project` (no
  cross-user access by guessing IDs).
- **Error handling**: raise `HTTPException` with accurate status codes
  (400/401/404/409/422/502 for upstream Groq failures) and consistent JSON
  error bodies; don't leak stack traces or upstream provider internals to the
  client. `services/llm.py` wraps Groq calls so network/timeout/HTTP errors
  raise a single `LLMServiceError`, which routes translate to a clean `502`
  instead of an unhandled `500`.
- **Async**: DB and outbound HTTP calls are `async def` using the async
  SQLAlchemy session and `httpx.AsyncClient`.
- **Migrations**: schema changes go through Alembic migrations, not manual
  DDL or `create_all` in production paths.

## Commands

```bash
pip install -r requirements.txt                            # install deps (run inside venv/)
uvicorn app.main:app --reload --reload-dir app --port 8000  # run the API locally
alembic upgrade head                                        # apply migrations
alembic revision --autogenerate -m "..."                    # create a migration after model changes
pytest                                                       # run tests
pytest tests/test_auth.py::test_login                       # run a single test
```

Note: `uvicorn --reload` watching the whole project root has been unreliable
on this machine (stalls silently on file changes, especially when `pip
install` touches files under `venv/`) — scope it to `--reload-dir app`, and if
a reload still looks stuck, kill and restart the process rather than trusting
it.
