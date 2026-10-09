# NOVA First Engineering Assignment: Vendor Service Area and Coverage

## Assignment goal
Build one integrated module that lets a vendor define where they serve customers, save the coverage, and edit it later. The same saved data must support activation and geographic matching.

## Ownership model
- One frontend engineer
- One backend engineer
- Work is expected to land as one integrated solution

## Shared contract and scope limits
- Agree on the supported area dataset and boundary behavior before implementation.
- Review the shared contract together; do **not** create separate frontend and backend definitions.
- Use a seeded vendor and the agreed authentication foundation.
- Excluded scope:
  - Maps
  - Automatic location detection
  - Travel pricing
  - AI suggestions
  - Full onboarding
  - Complete vendor matching

## Frontend scope
Build a mobile and desktop coverage form using NOVA’s existing design system.

### Required coverage modes
- **RADIUS**: a location plus a service radius
- **AREAS**: selected geographic areas

### Required UI behavior
- Load saved coverage
- Support editing existing coverage
- Show these states:
  - Loading
  - Validation
  - Saving
  - Saved
  - Failure
  - Stale-edit conflict

## Backend scope
Implement the existing draft contracts:
- `GET /v1/locations/search`
- `GET /v1/vendors/{id}/service-area`
- `PATCH /v1/vendors/{id}/service-area`

### Backend responsibilities
- Persist coverage in PostgreSQL
- Validate geographic inputs
- Enforce organization permissions
- Prevent stale updates
- Add an internal function that checks whether an event location falls within saved coverage
- No new public endpoint is required for eligibility checks

## Definition of done
- Coverage persists after reload
- Known inside/outside locations produce correct eligibility results
- Invalid coordinates, radius, and area IDs are rejected
- One organization cannot access or edit another vendor’s private coverage
- Concurrent edits return a clear conflict instead of silently overwriting data
- Deliver:
  - Integrated screen
  - Database migration
  - Tests
  - Short setup guide
- Both engineers demonstrate the complete working journey together

## Effort estimate
- 40-60 combined engineering hours total
- Approximate timeline: one working week with one frontend and one backend engineer, assuming repository, database, and authentication scaffolding already exist
- Foundation setup is additional

## Notes to keep in mind
- The area dataset and boundary behavior are intentionally contract-sensitive and must be agreed before implementation.
- This assignment focuses on service coverage persistence and eligibility logic, not broader marketplace matching.
