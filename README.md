# LEO Constellation Builder GUI

Web GUI to add satellites (by NORAD ID or pasted TLE), generate their
positions, and simulate the orbits in CesiumJS. It emits the **same**
`manifest.json` + `positions/*.csv` artifacts the ns-3 LEO pipeline consumes,
so the constellation you build here feeds Stage 2 (topology) and the
simulation directly.

## What it does

1. **Add satellites** — by NORAD catalog ID (offline demo synthesizes a
   plausible LEO orbit per ID) or by pasting a real TLE (parsed + validated).
2. **Generate positions** — propagates every staged satellite over your chosen
   duration/step, writing ECEF traces + manifest under `out/`.
3. **Simulate** — converts the traces to CZML and animates the orbits on the
   Cesium globe with a play/scrub timeline.

## Run

    pip install flask
    cd backend
    python3 app.py
    # open http://127.0.0.1:5000

No Cesium Ion token needed — it uses the bundled Natural Earth imagery.

## Architecture

    templates/index.html   entry panel + Cesium container
    static/app.js          satellite CRUD, generate, CZML -> Cesium
    static/style.css
    backend/app.py         Flask API (in-memory staging, generate endpoint)
    backend/propagate.py   position generation  (SWAP POINT — see below)
    backend/czml.py        ECEF traces -> Cesium CZML
    out/                   generated manifest.json + positions/*.csv

## Swapping in your real SGP4 pipeline

The demo ships a self-contained circular-orbit propagator so it runs with no
Skyfield/network. It is NOT SGP4-accurate — orbits are visually correct but
not precise. To use your real Stage-1 tool, replace the body of
`propagate_positions()` in `backend/propagate.py` with a call into
`gen_positions.py` (Skyfield SGP4 + TEME->ITRS). The GUI depends only on that
function's contract:

    propagate_positions(sats, start_utc, duration_s, step_s, out_dir) -> manifest
        sats = [{"norad_id", "name", "l1", "l2"}, ...]

and the manifest/CSV format is already identical, so `czml.py`, the API, and
the frontend need no changes. Two more production swaps:

- **Live TLE fetch**: in `app.py`, `demo_tle_for()` fabricates offline TLEs.
  Replace the `else` branch of `add_sat()` with `gen_positions.fetch_by_ids()`
  so a bare NORAD ID pulls the real current TLE from Celestrak.
- **Real SGP4 accuracy note**: once using Skyfield, drop the `--max-tle-age`
  guard's demo exemption; stale TLEs should warn as in the CLI tool.

## Notes

- State is in-memory and single-user (a demo server). For multi-user, back
  the staging area with a session or a small DB.
- The generated `out/manifest.json` is directly usable by
  `gen_topology.py --manifest out/manifest.json` and by the ns-3
  `LeoEphemerisNodeHelper`.
- CZML positions use `referenceFrame: FIXED` (ECEF), matching the trace
  frame, so Cesium shows the true Earth-fixed ground track and orbital-plane
  precession.
