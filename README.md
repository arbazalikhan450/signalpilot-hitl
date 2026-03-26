# SignalPilot with Human-in-the-Loop

Production-oriented scaffold for a social publishing system where AI drafts content, humans review it, and approved content is published asynchronously to social platforms.

## Architecture

- Backend: FastAPI + SQLAlchemy + Alembic
- Workflow engine: LangGraph state transitions for draft and review lifecycle
- Database: PostgreSQL
- Queue: Redis + RQ worker
- Frontend: React + Vite
- LLM layer: OpenAI API behind a swappable service
- Integrations: OAuth 2.0 scaffolding for X and LinkedIn
- Observability: structured logs + Prometheus metrics endpoint

## Project structure

```text
signalpilot-hitl/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── domain/
│   │   ├── integrations/
│   │   ├── services/
│   │   ├── workers/
│   │   └── workflows/
│   ├── migrations/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

## Core workflow

1. `POST /api/v1/generate-post` generates a platform-specific draft through the LLM service.
2. The LangGraph workflow marks the draft as `PENDING_APPROVAL`.
3. Reviewer uses the React dashboard to approve, edit, or reject.
4. Approved posts are transitioned to `APPROVED` or `SCHEDULED`.
5. An RQ worker pulls publish jobs and posts via the platform integration client.
6. Publish attempts are recorded in `publish_logs`.

## Data model

- `users`: system users and reviewers
- `social_accounts`: OAuth-linked social identities and encrypted tokens
- `posts`: generated content, schedule, state, LLM metadata
- `approvals`: reviewer decisions and edit history
- `publish_logs`: publish attempts, failures, and platform responses

## API endpoints

- `POST /api/v1/generate-post`
- `GET /api/v1/posts`
- `POST /api/v1/approve`
- `POST /api/v1/reject`
- `POST /api/v1/publish`
- `GET /api/v1/oauth/{platform}/start`
- `GET /api/v1/oauth/x/callback`
- `GET /api/v1/oauth/linkedin/callback`
- `GET /health`
- `GET /metrics`

## Local setup

1. Copy `.env.example` to `.env`.
2. Fill in OpenAI, X, and LinkedIn credentials.
3. Start infra:

```bash
docker compose up --build
```

4. Run database migrations inside the API container:

```bash
docker compose exec api alembic upgrade head
```

5. Open:

- API docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:5173`
- Metrics: `http://localhost:8000/metrics`

## Local development without Docker

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Worker

```bash
cd backend
rq worker publish -u redis://localhost:6379/0
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## OAuth notes

- X OAuth 2.0 PKCE is scaffolded but still uses placeholder PKCE generation values. Replace those with per-session verifier/challenge storage before production launch.
- LinkedIn callback wiring is present, but profile lookup should be added to resolve the real `account_identifier`.
- Tokens are encrypted at rest using a Fernet wrapper derived from `TOKEN_ENCRYPTION_KEY`.

## Production hardening still recommended

- Replace demo user creation with real authentication and RBAC.
- Add persistent scheduler for future-dated posts instead of queueing all approvals immediately.
- Add token refresh orchestration before publish attempts.
- Add moderation, policy checks, and content linting before approval.
- Add webhook-driven feedback loop for engagement analytics.
- Add tests, circuit breakers, and dead-letter queue handling.

## Bonus extension ideas

- Multi-platform fan-out from a single content brief
- Content calendar and campaign grouping
- Approval SLAs and escalation routing
- Engagement feedback loop to refine prompts over time
