# Чокнемся

Full-stack monorepo with a Vite/React frontend and FastAPI backend.

## Run the stack

```sh
docker compose up --build
```

The frontend is available at `http://localhost:5173`, the backend at
`http://localhost:8000`, and FastAPI documentation at `http://localhost:8000/docs`.

Stop the stack with:

```sh
docker compose down
```

## Frontend

The authentication and registration flow currently uses an in-memory mock service.
It does not persist credentials or call the backend because an authentication API is
not yet defined in the project contracts.

Run locally:

```sh
cd frontend
npm ci
npm run dev
```

Run tests and checks:

```sh
npm test
npm run lint
npm run build
```

With the Compose stack running, the canonical frontend test command is:

```sh
docker compose exec frontend npm test
```

## Storybook

Start Storybook locally:

```sh
cd frontend
npm run storybook
```

Open `http://localhost:6006`. To run Storybook in a one-off container:

```sh
docker compose run --rm --service-ports frontend npm run storybook -- --host 0.0.0.0
```

Build the static Storybook bundle with `npm run build-storybook`.

## Backend

Run backend tests inside Compose:

```sh
docker compose exec backend pytest
```

For service-specific development, run `fastapi dev app/main.py` from `backend/`.
