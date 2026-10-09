# NOVA Vendor Service Area

An assignment-sized service coverage flow with a Next.js frontend, FastAPI backend, and PostgreSQL persistence.

## Run the integrated stack

From the repository root:

```sh
docker compose up --build
```

The root Compose file owns PostgreSQL and includes the API service from `backend/compose.yaml`. Run the Next.js app separately from `frontend/` as described below. The API docs are at <http://localhost:8000/docs>. Sign in with `vendor-demo@nova.test` / `NOVA-demo-2026!`; a second seeded account `other-demo@nova.test` belongs to a separate organization for permission demonstrations.

To stop the stack, run `docker compose down`. Add `-v` to remove the local database volume and its saved coverage.

## Run backend by itself

The backend Compose file defines the API service, which is intended to be included by the root Compose file where PostgreSQL is defined. Run Compose from the repository root so the API can connect to the root `db` service. The backend folder still owns its Dockerfile and service configuration.

## Run frontend locally

Start the backend using either Compose setup, then in `frontend/`:

```sh
cp .env.example .env.local
npm install
npm run dev
```

The frontend proxies `/api` to the API at `http://127.0.0.1:8000/v1`, so signing in works from both `localhost:3000` and `127.0.0.1:3000`. If the API uses another address, set `API_PROXY_TARGET` in `frontend/.env.local` and restart Next.js. The frontend is intentionally not containerized by Compose.

## Contract and behavior

- `GET /v1/locations/search?q=...` proxies location searches to OpenStreetMap Nominatim. The frontend searches as the user types with a debounce; the API caches results for one hour and limits uncached requests from this API process to at most one per second. A small fallback corrects common place-name typos when the exact query has no result.
- `GET /v1/service-areas` returns the canonical supported-area catalog and dataset version used by both the frontend and backend.
- `POST /v1/auth/login` verifies seeded credentials and returns an expiring bearer token; `GET /v1/auth/me` returns the signed-in user.
- `GET /v1/vendors/{id}/service-area` loads coverage and revision.
- `PATCH /v1/vendors/{id}/service-area` saves coverage when `expected_revision` matches; outdated edits return `409 stale_service_area`.
- The backend eligibility function is `check_event_eligibility` in `backend/app/api/routes.py` and is intentionally internal.
- Radius distance uses Haversine with an inclusive boundary (`distance <= radius`).
- The area fixture is `demo-us-metro-v1`: three metro areas represented by approximate circles with inclusive boundaries. The chosen areas, centers, radii, coordinate rules, and boundary behavior are recorded in [docs/coverage-contract.md](docs/coverage-contract.md). NOVA's production boundaries require an approved authoritative dataset before production use.
- The location picker displays OpenStreetMap attribution. Nominatim is configured with `NOMINATIM_BASE_URL` and `GEOCODING_USER_AGENT`, so the endpoint can be changed without a frontend update. Public Nominatim is a limited community service; production volume should use an appropriately provisioned geocoding provider or operated instance.
- A seeded walkthrough account and repeatable end-to-end demonstration are documented in [docs/demo-runbook.md](docs/demo-runbook.md). The API demo script verifies saved edits and invokes the internal eligibility function without adding a public matching endpoint.

## Demo authentication boundary

The login endpoint issues an eight-hour HMAC-signed bearer token. Passwords are stored as salted PBKDF2 hashes, and protected API requests load the user from the database and derive organization ownership from that record. The frontend keeps the token in session storage for this assignment demo. Replace this local login/token implementation with NOVA's established identity provider before production; set a strong `AUTH_SECRET` in the root `.env` file. Vendor reads and writes are restricted by organization, and cross-organization access returns 404.

## Migrations and tests

```sh
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
alembic upgrade head
python -m app.seed
pytest
```

The API tests use an isolated in-memory SQLite database and exercise the route contract, persistence across requests, invalid geographic input, organization isolation, and stale-edit conflicts. The production runtime remains PostgreSQL.

Set `DATABASE_URL` for a local PostgreSQL instance before running Alembic or tests.
