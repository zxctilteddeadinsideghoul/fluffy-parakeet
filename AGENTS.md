# Repository Guidelines

## Architecture and Required Structure

This is a full-stack monorepo. Create new files in this structure from the start:

```text
.
|-- frontend/                 # Vite + React application
|   |-- src/
|   |   |-- components/
|   |   |-- features/
|   |   |-- services/        # API clients
|   |   `-- assets/
|   |-- public/
|   |-- tests/
|   |-- package.json
|   `-- Dockerfile
|-- backend/                  # Python + FastAPI application
|   |-- app/
|   |   |-- api/              # Routers and dependencies
|   |   |-- core/             # Configuration
|   |   |-- models/
|   |   |-- schemas/
|   |   |-- services/
|   |   `-- main.py
|   |-- tests/
|   |-- pyproject.toml
|   `-- Dockerfile
|-- compose.yaml
|-- .env.example
`-- README.md
```

Agents must preserve this separation. Never place React or Python source in the root. Create directories when they gain a concrete responsibility; avoid empty placeholders.

## Mandatory Data and Domain Contracts

Before planning, implementing, or reviewing any product change, agents MUST read and follow both contract documents in full:

- `docs\CONTRACTS_DATA.md`
- `docs\DOMAIN_ENTITIES.md`

Treat these files as the source of truth for stored models, API DTOs, commands, events, invariants, state transitions, aggregate boundaries, privacy rules, and frontend types. Code, database schemas, tests, and documentation MUST remain consistent with both documents. Do not silently resolve `TBD` items, invent missing fields or transitions, or merge independently modeled user consents.

If either file is missing, inaccessible, truncated, contradictory, or does not provide enough context for the requested change, the agent MUST explicitly identify the missing or ambiguous contract information and stop work. Do not infer a contract or implement a provisional interpretation; resume only after the contracts or requirements are clarified.

## Build, Test, and Development Commands

Docker Compose is the canonical interface. Keep these root commands working:

- `docker compose up --build` - build images and start the complete stack.
- `docker compose down` - stop and remove local containers.
- `docker compose exec frontend npm test` - run frontend tests.
- `docker compose exec backend pytest` - run backend tests.

Service-specific commands include `npm run dev` in `frontend/` and `fastapi dev app/main.py` in `backend/`. Document additions in `README.md`.

## Coding Style and Naming

Use TypeScript, two-space indentation, functional React components, and `PascalCase.tsx` component names. Use `camelCase` for functions; hooks begin with `use`. Group feature code under `frontend/src/features/<feature>/`.

Use Python type hints, four-space indentation, `snake_case` modules/functions, and `PascalCase` classes. Keep route handlers thin and business logic in `services/`. Use Ruff for Python and ESLint/Prettier for frontend code.

## Testing Guidelines

Use Vitest with React Testing Library and pytest. Name tests `*.test.tsx` and `test_*.py`. Cover new behavior, validation, API errors, and bug fixes. Do not depend on production credentials or external services.

## Configuration and Security

Read configuration from environment variables. Commit safe placeholders in `.env.example`; never commit `.env` or secrets. Prefix browser variables with `VITE_` and never expose secrets through them. Containers communicate by Compose service name, not `localhost`.

## Commits and Pull Requests

Use imperative, scoped commits: `feat(frontend): add login form` or `fix(backend): validate token expiry`. Pull requests must describe changes, verification, and linked issues; include UI screenshots. Highlight migrations, environment variables, ports, and dependencies.
