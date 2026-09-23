# ayaan1208

A minimal full-stack TypeScript demo app used to exercise a Cloud Agent development environment.

## Stack

- **Frontend** (`web/`): Vite + React + TypeScript. Dev server on port `5173`, proxies `/api` to the backend.
- **Backend** (`server/`): Express + TypeScript REST API with an in-memory Todo store. Listens on port `3001`.
- npm workspaces tie the two packages together.

## Getting started

```bash
npm ci            # install all workspace dependencies
npm run dev       # start API (3001) and web (5173) together
```

Then open http://localhost:5173.

## Useful scripts

| Command | Description |
| --- | --- |
| `npm run dev` | Run API + web dev servers concurrently |
| `npm run dev:server` | Run only the Express API (port 3001) |
| `npm run dev:web` | Run only the Vite dev server (port 5173) |
| `npm run build` | Type-check + build both packages |
| `npm run typecheck` | Type-check both packages |

## API

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Liveness probe |
| `GET` | `/api/todos` | List todos |
| `POST` | `/api/todos` | Create a todo (`{ "title": string }`) |
| `PATCH` | `/api/todos/:id` | Update `completed` / `title` |
| `DELETE` | `/api/todos/:id` | Delete a todo |

## Cloud Agent environment

`.cursor/environment.json` installs dependencies with `npm ci` and launches the API and web dev servers as named terminals.
