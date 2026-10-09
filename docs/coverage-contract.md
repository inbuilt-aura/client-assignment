# Vendor coverage contract

## Assignment dataset decision

For this assignment, the supported geographic areas are the three entries in the API's `GET /v1/service-areas` catalog, dataset version `demo-us-metro-v1`:

| ID | Area | Representative places | Center | Radius |
| --- | --- | --- | --- | ---: |
| `sf-bay` | San Francisco Bay Area | San Francisco, Oakland, San Jose | 37.7749, -122.4194 | 90 km |
| `la-metro` | Los Angeles Metro | Los Angeles, Long Beach, Anaheim | 34.0522, -118.2437 | 75 km |
| `nyc-metro` | New York City Metro | New York, Newark, Jersey City | 40.7128, -74.0060 | 70 km |

These are intentionally approximate circles for the assignment dataset. A location is inside an area when its Haversine distance from that area's center is less than or equal to the listed radius. The boundary is inclusive. Radius coverage uses the same inclusive distance rule around the vendor-selected location. This is the contract used by the API, frontend catalog, validation, and eligibility logic.

The catalog endpoint is the frontend's only source for area IDs, labels, and descriptions; the backend's canonical catalog also drives validation and eligibility. Changing area membership or geometry requires changing the dataset version and reviewing expected eligibility results.

This records the assignment's demo dataset decision, not a claim that the approximate circles are NOVA's production service boundaries. Production use requires NOVA to approve an authoritative dataset and boundary rule.

## Request constraints

- Coordinates use WGS84 decimal degrees: latitude from -90 to 90 and longitude from -180 to 180.
- Radius coverage requires a radius greater than 0 and no more than 500 km.
- Area coverage requires one or more unique IDs from the catalog.
- A save includes the revision returned by GET. If another save has advanced it, PATCH returns `409 stale_service_area` and preserves the latest value.
