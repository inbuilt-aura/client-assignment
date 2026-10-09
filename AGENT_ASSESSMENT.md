# Agent Assessment: NOVA Vendor Service Area

## Repository shape
This repository is a small monorepo:
- `frontend/` contains a Next.js app
- `backend/` contains a FastAPI service with PostgreSQL persistence
- The root `compose.yaml` includes the backend service and defines PostgreSQL

## What the repo already does well

### Frontend
- Provides a polished service coverage screen for desktop and mobile
- Supports both coverage modes:
  - `RADIUS`
  - `AREAS`
- Loads saved coverage on page load
- Supports editing existing coverage
- Displays:
  - loading
  - validation
  - saving
  - success
  - generic failure
  - stale-edit conflict
- Uses a seeded login flow and session storage token handling
- Includes a location search flow that talks to the backend `/v1/locations/search`

### Backend
- Implements:
  - `GET /v1/locations/search`
  - `GET /v1/vendors/{id}/service-area`
  - `PATCH /v1/vendors/{id}/service-area`
- Persists service coverage in PostgreSQL
- Uses a revision field to prevent stale overwrites
- Enforces organization scoping through vendor ownership checks
- Returns `404` when another organization tries to access a private vendor
- Validates:
  - latitude / longitude
  - radius range
  - known area IDs
  - duplicate area IDs
- Includes an internal eligibility helper:
  - `check_event_eligibility(...)`
- Uses inclusive radius matching (`distance <= radius`)

## What is not fully complete or still constrained

### Contract / dataset gap
- The repo ships with a demo area dataset:
  - `demo-us-metro-v1`
- The supported area dataset is still explicitly marked as a placeholder
- Boundary behavior for the final client-approved dataset still needs confirmation before production use

### Validation / acceptance evidence gap
- Backend unit tests pass, but there are no end-to-end HTTP acceptance tests proving the full API journey against a running database
- The integrated Docker Compose flow could not be started in this environment because the Docker CLI is not installed here
- The frontend build and TypeScript check passed after installing dependencies, but the repo relies on local dev setup for the live end-to-end flow

### Product scope gap
- Maps are not implemented, which matches the exclusions
- Automatic location detection is not implemented, which matches the exclusions
- Travel pricing, AI suggestions, onboarding expansion, and full matching are not implemented, which also matches the exclusions

## Evidence from validation
- Backend tests: `6 passed`
- Frontend:
  - `npm ci`
  - `npm run lint`
  - `npm run build`
- Docker Compose:
  - could not be executed here because `docker` is not available in the current environment

## Overall assessment
The repo already covers the core assignment well:
- it has the required frontend screen,
- the required backend contracts,
- PostgreSQL persistence,
- permission checks,
- and stale-write protection.

The main remaining business-risk item is the shared geographic dataset contract: the code uses a demo metro-area fixture that must be replaced or formally approved before production use.

## Suggested next step
Confirm the authoritative area dataset and boundary rules, then add at least one end-to-end API test that exercises:
- load coverage
- save coverage
- stale-edit conflict
- inside/outside eligibility
