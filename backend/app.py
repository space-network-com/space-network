"""
app.py — Flask backend for the LEO constellation GUI.

Endpoints:
  GET  /                       the GUI page
  GET  /api/satellites         list staged satellites
  POST /api/satellites         add one (by pasted TLE, or NORAD id + demo TLE)
  DELETE /api/satellites/<id>  remove one
  POST /api/generate           run propagation over all staged sats -> CZML
  GET  /api/czml               fetch the last generated CZML (Cesium loads this)

State is in-memory (single-user demo). The generate step writes the same
manifest.json + positions/*.csv that the ns-3 pipeline consumes, under ./out.
"""

import io
import pathlib
from datetime import datetime, timezone

from flask import Flask, jsonify, request, send_from_directory

from propagate import propagate_positions, parse_tle, semi_major_axis
from czml import build_czml

APP_DIR = pathlib.Path(__file__).resolve().parent
ROOT = APP_DIR.parent
OUT_DIR = ROOT / "out"

app = Flask(__name__, static_folder=str(ROOT / "static"),
            template_folder=str(ROOT / "templates"))

# In-memory staging area: norad_id -> {norad_id, name, l1, l2}
_SATS = {}
_LAST_CZML = None


# ---------------------------------------------------------------------------
# Demo TLE synthesis: when the user adds a bare NORAD id (no network here),
# fabricate a plausible LEO TLE so the demo is usable offline. Replace with a
# real Celestrak fetch (see gen_positions.fetch_by_ids) in production.
# ---------------------------------------------------------------------------

def demo_tle_for(norad_id: int, plane: int = 0, slot: int = 0):
    inc = 53.0
    raan = (plane * 30.0) % 360.0
    ma = (slot * 45.0) % 360.0
    mm = 15.05  # ~550 km
    l1 = f"1 {norad_id:05d}U 24001A   24001.00000000  .00000000  00000-0  00000-0 0  9990"
    l2 = (f"2 {norad_id:05d} {inc:8.4f} {raan:8.4f} 0001000 "
          f"000.0000 {ma:8.4f} {mm:11.8f}00000")
    return l1, l2


@app.route("/")
def index():
    return send_from_directory(app.template_folder, "index.html")


@app.route("/static/<path:p>")
def static_files(p):
    return send_from_directory(app.static_folder, p)


@app.route("/api/satellites", methods=["GET"])
def list_sats():
    return jsonify(sorted(_SATS.values(), key=lambda s: s["norad_id"]))


@app.route("/api/satellites", methods=["POST"])
def add_sat():
    data = request.get_json(force=True)
    l1 = (data.get("l1") or "").strip()
    l2 = (data.get("l2") or "").strip()
    name = (data.get("name") or "").strip()

    try:
        if l1 and l2:
            elem = parse_tle(l1, l2)             # validates
            norad = elem["norad"]
        else:
            norad = int(data["norad_id"])
            # offline demo: synthesize; vary plane/slot by count for spread
            k = len(_SATS)
            l1, l2 = demo_tle_for(norad, plane=k % 12, slot=(k // 12) % 8)
            elem = parse_tle(l1, l2)
    except (ValueError, KeyError, TypeError) as e:
        return jsonify({"error": f"invalid input: {e}"}), 400

    if norad in _SATS:
        return jsonify({"error": f"NORAD {norad} already added"}), 409

    a = semi_major_axis(elem["mean_motion"])
    _SATS[norad] = {
        "norad_id": norad,
        "name": name or f"SAT-{norad}",
        "l1": l1, "l2": l2,
        "altitude_km": round((a - 6371000.0) / 1000.0, 1),
        "inclination_deg": round(__import__("math").degrees(elem["inc"]), 2),
    }
    return jsonify(_SATS[norad]), 201


@app.route("/api/satellites/<int:norad>", methods=["DELETE"])
def del_sat(norad):
    _SATS.pop(norad, None)
    return "", 204


@app.route("/api/satellites", methods=["DELETE"])
def clear_sats():
    _SATS.clear()
    return "", 204


@app.route("/api/generate", methods=["POST"])
def generate():
    global _LAST_CZML
    if not _SATS:
        return jsonify({"error": "no satellites added"}), 400
    p = request.get_json(silent=True) or {}
    duration = float(p.get("duration_s", 5400))   # default ~1.5 orbits
    step = float(p.get("step_s", 30))

    start = datetime.now(timezone.utc).replace(microsecond=0)
    sats = [{"norad_id": s["norad_id"], "name": s["name"],
             "l1": s["l1"], "l2": s["l2"]} for s in _SATS.values()]

    manifest = propagate_positions(sats, start, duration, step, OUT_DIR)
    _LAST_CZML = build_czml(manifest, OUT_DIR)

    return jsonify({
        "ok": True,
        "num_satellites": manifest["num_satellites"],
        "num_samples": manifest["num_samples"],
        "step_s": manifest["step_s"],
        "duration_s": duration,
        "manifest_path": str((OUT_DIR / "manifest.json")),
        "satellites": manifest["satellites"],
    })


@app.route("/api/czml", methods=["GET"])
def get_czml():
    if _LAST_CZML is None:
        return jsonify({"error": "nothing generated yet"}), 404
    return jsonify(_LAST_CZML)


if __name__ == "__main__":
    OUT_DIR.mkdir(exist_ok=True)
    app.run(host="127.0.0.1", port=5000, debug=True)
