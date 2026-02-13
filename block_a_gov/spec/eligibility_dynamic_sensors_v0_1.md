# eligibility_dynamic_sensors_v0_1

## Purpose
Define LIVE/STUB behavior for the two Eligibility dynamic sensors (`wE`, `wF`) with deterministic fallback policy.

## Scope
Applies to `runner_eligibility.py` only.

## Sensors in scope (Eligibility lane)
- `wE` via DS_Z endpoint: `/sensor/bureau_spike_score`
- `wF` via DS_Z endpoint: `/sensor/market_snapshot`

Out of scope for this contract:
- ORIGINATE post-gate sensors (`wB`, `wC`) are managed in ORIGINATE lane.

## Input dependency
The runner consumes `application_intake_v0_1` and expects:
- `meta_request_id`
- `meta_client_id`
- `meta_as_of_ts` (optional for LIVE market query)
- `dynamic_sensors_for_eligibility` STUB values (fallback source)

## Runtime modes
- `STUB`: use only intake-provided `dynamic_sensors_for_eligibility`.
- `LIVE`: query DS_Z for `wE` and `wF`; if query fails, fallback to intake STUB values per sensor.

## LIVE query contract
- `wE` request:
  - `GET {sensor_base_url}/sensor/bureau_spike_score?client_id=<meta_client_id>&lookback_hours=24&request_id=<meta_request_id>`
- `wF` request:
  - Primary: `GET {sensor_base_url}/sensor/market_snapshot?request_id=<meta_request_id>&as_of=<meta_as_of_ts>`
  - Retry rule: on HTTP 400 with `as_of`, retry once without `as_of`.

## Mapping to Eligibility fields
- `wE` response `bureau_spike_score_24h` maps to
  - `dyn_bureau_employment_verified = (bureau_spike_score_24h < BUREAU_UNVERIFIED_THR)`
  - default threshold: `0.8` (override allowed via canonical alias parameter `BUREAU_UNVERIFIED_THR`)
- `wF` response `market_stress_score_7d` maps to
  - `dyn_market_stress_score_7d`

## Fallback policy (per sensor)
- If `wE` LIVE call fails -> keep STUB value from intake for `dyn_bureau_employment_verified`.
- If `wF` LIVE call fails (including retry failure) -> keep STUB value from intake for `dyn_market_stress_score_7d`.
- Fallback events are logged to stderr as `[ELIGIBILITY][LIVE->STUB] ...`.

## Output traceability
`eligibility_agent_status_v0_1` includes:
- `meta_sensor_mode_used`:
  - `STUB` when no LIVE calls attempted
  - `LIVE` when LIVE path resolved without fallback
  - `LIVE_FALLBACK` when any sensor fell back to STUB

## Reliability constraints (PoC)
- Sensor timeout configurable (`--sensor-timeout-ms`).
- Missing/failed LIVE must not break the runner.
- Decision logic remains deterministic given resolved sensor values.

## Versioning policy
- Additive changes only.
- Existing mode semantics and field names remain stable in `v0.1`.
