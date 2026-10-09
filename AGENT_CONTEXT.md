# Agent Context: NOVA Vendor Service Area Assignment

This document is the working summary for the agent handling the NOVA vendor service-area assignment. It complements the client requirements document in [CLIENT_REQUIREMENTS.md](./CLIENT_REQUIREMENTS.md) and gives a repo-specific assessment of what the current codebase does and what remains to be confirmed or completed.

## 1) Client requirement summary

The assignment is to build one integrated module that lets a vendor define where they serve customers, save that coverage, and edit it later. The saved coverage must support activation and geographic matching.

### Frontend requirements
- Build a mobile and desktop coverage form using the current NOVA design system.
- Support two coverage modes:
  - RADIUS: a selected location plus a service radius
  - AREAS: selected geographic areas
- Load saved coverage and allow editing.
- Show states for:
  - loading
  - validation
  - saving
  - saved
  - failure
  - stale-edit conflict

### Backend requirements
Implement the existing draft contracts:
- GET /v1/locations/search
- GET /v1/vendors/{id}/service-area
- PATCH /v1/vendors/{id}/service-area

Required backend behavior:
- Persist coverage in PostgreSQL
- Validate geographic inputs
- Enforce organization permissions
- Prevent stale updates
- Add an internal function to check whether an event location falls within saved coverage
- No new public endpoint is required

### Shared contract and scope limits
- The supported area dataset and boundary behavior must be agreed before implementation.
- The frontend and backend must use the same shared contract.
- The implementation should use a seeded vendor and agreed authentication foundation.
- Excluded items:
  - maps
  - auto-detection
  - travel pricing
  - AI suggestions
  - full onboarding
  - full vendor matching

### Definition of done
- Coverage persists after reload.
- Known inside/outside locations produce correct eligibility results.
- Invalid coordinates, radius, and area IDs are rejected.
- One organization cannot access or edit another vendor's private coverage.
- Concurrent edits return a conflict instead of silently overwriting data.
- Deliverables include:
  - integrated screen
  - database migration
  - tests
  - short setup guide

### Focus area
This is a service coverage and eligibility assignment, not a broad marketplace-matching project.

## 2) Repo shape and architecture

This repo is a monorepo with separate frontend and backend projects:
- frontend/: Next.js app
- backend/: FastAPI API + SQLAlchemy + PostgreSQL persistence
- root compose.yaml: orchestrates Postgres and backend service

The repo includes:
- frontend coverage form UI
- backend API routes and service validation
- database models and migration files
- tests covering coverage logic
- seeded auth and demo vendor data

## 3) What the current repo already does well

### Frontend status
Implemented in [frontend/components/CoverageForm.tsx](./frontend/components/CoverageForm.tsx):
- UI supports both RADIUS and AREAS modes
- location search integrates with the backend geocoder
- loading state is displayed while fetching coverage
- validation state is enforced before save
- saving and saved/success states are shown
- failure and stale conflict states are handled
- editing of previously saved coverage is supported
- token handling and login flow are in place via [frontend/lib/api.ts](./frontend/lib/api.ts)

### Backend status
Implemented across [backend/app/api/routes.py](./backend/app/api/routes.py), [backend/app/services/coverage.py](./backend/app/services/coverage.py), and [backend/app/models/service_area.py](./backend/app/models/service_area.py):
- GET /v1/locations/search is implemented with a server-side Nominatim proxy and caching
- GET /v1/vendors/{id}/service-area is implemented
- PATCH /v1/vendors/{id}/service-area is implemented
- PostgreSQL persistence via SQLAlchemy model and migration
- revision check prevents stale overwrites with 409 stale_service_area
- organization-based access control is enforced by vendor ownership checks
- invalid area IDs are rejected
- radius and location validation are enforced using the geo service
- internal eligibility helper exists: check_event_eligibility
- radius boundary is inclusive (distance <= radius)

### Data and contract status
- Area fixture and logic are configured in [backend/app/core/areas.py](./backend/app/core/areas.py).
- The dataset is a demo metro-area fixture, not yet an approved production dataset.
- The repo documents this as a placeholder requiring a client-approved dataset before production.

## 4) What is done vs. not done

### Done
- Core frontend form exists
- Core backend endpoints exist
- DB persistence and migration exist
- Permission checks exist
- Stale write protection exists
- Coverage validation exists
- Internal eligibility logic is implemented
- Tests exist and pass

### Partially complete or contract-sensitive
- The area dataset is demo-only and marked as a placeholder.
- The boundary behavior is implemented for the demo data but must be confirmed against the final authoritative area dataset.
- The repo demonstrates the assignment flow, but not a fully production-certified shared contract.

### Explicitly excluded and not present
- maps
- auto location detection
- travel pricing
- AI suggestions
- full onboarding
- full vendor matching

These are absent, which matches the client exclusions.

## 5) Validation performed in this environment

I ran the repo-level checks that are feasible without Docker.

### Backend validation
Command used:
- from repo root: python -m pytest backend/tests -q using the workspace venv

Latest result:
- 6 passed in 0.49s

### Frontend validation
Command used:
- from frontend/: npm run lint
- from frontend/: npm run build

Latest result:
- `npm run lint` passed
- `npm run build` passed
- Next.js production build generated the expected `/`, `/login`, and not-found routes

### Docker / compose validation
- Docker is unavailable in this environment, so the full PostgreSQL/API Compose journey could not be executed here.
- This is an environment limitation, not a reported application failure.
- The intended full-stack command remains `docker compose up --build` from the repository root.

## 6) Overall repo assessment

This repository is a strong implementation of the assignment and already satisfies most of the core expected scope:
- required UI patterns exist
- both coverage modes exist
- persistence and revision handling exist
- permission checks are in place
- stale conflict handling exists
- backend tests pass
- frontend build is green

The main remaining business-risk item is the shared geographic dataset contract: the repo uses a demo metro-area fixture that needs to be replaced or formally approved before production use.

## 7) Final status

### Client requirements satisfied by the current repository
- Integrated coverage screen: present
- RADIUS and AREAS coverage: present
- Saved coverage load/edit flow: present
- Loading, validation, saving, saved, failure, and stale-conflict states: present
- Required API contracts: present
- PostgreSQL migration and persistence: present
- Geographic validation: present
- Organization permission checks: present
- Stale update protection: present
- Internal eligibility function: present
- Automated backend and frontend validation: passing
- Excluded features: not implemented, matching the requested scope limits

### Not yet suitable for unconditional production sign-off
- The area dataset is explicitly a demo fixture (`demo-us-metro-v1`).
- Its circular boundary approximation is suitable for the assignment demo but must be replaced or formally approved by the client.
- The final boundary rule (inclusive or exclusive at the boundary) must be agreed for the authoritative dataset.
- A running Docker/PostgreSQL end-to-end acceptance demonstration remains to be performed in an environment with Docker.

## 8) Recommended next step

Confirm the authoritative area dataset and boundary rules, then add at least one higher-level API test covering:
- load coverage
- save coverage
- stale revision conflict
- inside/outside eligibility

This is the most important remaining sign-off step before calling the assignment production-ready. After the dataset decision, add or run an API-level acceptance test covering load, save, stale conflict, permissions, and inside/outside eligibility against PostgreSQL.
