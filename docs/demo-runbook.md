# Coverage journey demonstration

This walkthrough demonstrates the integrated UI, API, database persistence, edits, and internal geographic matching. It uses a dedicated seeded walkthrough vendor so it does not alter the normal `vendor-demo` account.

## Start the app

From the repository root:

```sh
docker compose up --build -d
```

In another terminal, start the frontend from `frontend/`:

```sh
npm run dev
```

Open <http://localhost:3000/login> and sign in with:

- Email: `coverage-walkthrough@nova.test`
- Password: `NOVA-demo-2026!`

## Demonstrate the UI journey

1. Select **Within a radius**.
2. Search for **New York City**, select a result, and set the radius to `25` km.
3. Save the coverage and show the saved confirmation.
4. Reload the page and show that the selected location and radius persisted.
5. Change the radius to `40` km and save again.

The dedicated account can be reset for another live UI walkthrough by deleting its row from `vendor_service_areas`; the next save starts at revision zero. Do not delete the vendor or user rows.

## Verify the API journey and eligibility

From `backend/`, with Python dependencies installed and the Compose database/API running:

```sh
python -m app.seed
python -m scripts.demo_journey
```

The script signs in over HTTP, checks the user/vendor association, saves a 25 km radius, reloads it, edits it to 40 km, and invokes the internal `check_event_eligibility` function against PostgreSQL. It checks the known inside point at New York City and outside point at Los Angeles. It leaves the dedicated walkthrough vendor with the 40 km coverage so it can be inspected in the UI.

For a two-engineer demonstration, one person can drive the browser journey while the other runs the script and points out the persisted revision and eligibility results. The script uses the running API for all public operations; eligibility remains an internal function and is deliberately not exposed as an API endpoint.
