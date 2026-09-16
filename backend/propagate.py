"""
propagate.py — position generation for the LEO GUI.

Emits the SAME artifacts as gen_positions.py (Stage 1):
    <out>/manifest.json
    <out>/positions/<NORAD_ID>.csv   t_offset_s,x_m,y_m,z_m,vx_mps,vy_mps,vz_mps
frame: ECEF/ITRS, meters and m/s.

This ships a self-contained demo propagator (no Skyfield / no network) so the
GUI runs anywhere. It parses the orbit shape from the TLE mean-motion and
inclination and advances a circular orbit in an Earth-fixed frame — good
enough to see real, distinct orbits in Cesium. It is NOT SGP4-accurate.

=====================================================================
TO USE YOUR REAL PIPELINE: replace the body of propagate_positions() with a
call into gen_positions.py (Skyfield SGP4 + proper TEME->ITRS). The GUI only
depends on this function's contract:
    propagate_positions(sats, start_utc, duration_s, step_s, out_dir) -> manifest dict
where sats = [{"norad_id": int, "name": str, "l1": str, "l2": str}, ...]
=====================================================================
"""

import csv
import json
import math
import pathlib
from datetime import datetime, timezone

MU = 3.986004418e14          # Earth GM [m^3/s^2]
EARTH_RADIUS_M = 6371000.0
OMEGA_EARTH = 7.2921159e-5   # Earth rotation rate [rad/s]


# ----------------------------------------------------------------------
# TLE parsing (enough for the demo propagator; also validates input)
# ----------------------------------------------------------------------

def parse_tle(l1: str, l2: str):
    """Extract the orbital elements the demo needs from TLE lines 1 & 2.
    Raises ValueError on malformed input so the GUI can report it."""
    l1, l2 = l1.strip(), l2.strip()
    if not (l1.startswith("1 ") and l2.startswith("2 ")):
        raise ValueError("TLE lines must start with '1 ' and '2 '")
    try:
        norad = int(l2[2:7])
        inc = math.radians(float(l2[8:16]))             # inclination [rad]
        raan = math.radians(float(l2[17:25]))           # RAAN [rad]
        ecc = float("0." + l2[26:33].strip())           # eccentricity
        argp = math.radians(float(l2[34:42]))           # arg of perigee [rad]
        mean_anom = math.radians(float(l2[43:51]))      # mean anomaly [rad]
        mean_motion = float(l2[52:63])                  # revs/day
    except (ValueError, IndexError) as e:
        raise ValueError(f"could not parse TLE line 2: {e}")
    return {
        "norad": norad, "inc": inc, "raan": raan, "ecc": ecc,
        "argp": argp, "mean_anom": mean_anom, "mean_motion": mean_motion,
    }


def semi_major_axis(mean_motion_rev_day: float) -> float:
    n = mean_motion_rev_day * 2.0 * math.pi / 86400.0   # rad/s
    if n <= 0:
        raise ValueError("mean motion must be positive")
    return (MU / (n * n)) ** (1.0 / 3.0)


# ----------------------------------------------------------------------
# Demo propagator: circular orbit in ECEF
# ----------------------------------------------------------------------

def _demo_state(elem, a, t):
    """ECEF position+velocity at time t [s] for a circular orbit approx.
    Builds the orbit in the perifocal-ish plane, rotates by inclination and
    RAAN into ECI, then rotates by -Earth_rotation*t into ECEF."""
    n = math.sqrt(MU / a**3)              # mean motion [rad/s]
    theta = elem["mean_anom"] + elem["argp"] + n * t

    # position/velocity in orbital plane
    xp, yp = a * math.cos(theta), a * math.sin(theta)
    vxp, vyp = -a * n * math.sin(theta), a * n * math.cos(theta)

    # rotate by inclination about x, then RAAN about z  -> ECI
    ci, si = math.cos(elem["inc"]), math.sin(elem["inc"])
    yr, zr = yp * ci, yp * si
    vyr, vzr = vyp * ci, vyp * si
    cr, sr = math.cos(elem["raan"]), math.sin(elem["raan"])
    xe = xp * cr - yr * sr
    ye = xp * sr + yr * cr
    ze = zr
    vxe = vxp * cr - vyr * sr
    vye = vxp * sr + vyr * cr
    vze = vzr

    # ECI -> ECEF (rotate by -Earth rotation)
    g = -OMEGA_EARTH * t
    cg, sg = math.cos(g), math.sin(g)
    x = xe * cg - ye * sg
    y = xe * sg + ye * cg
    z = ze
    # velocity includes the frame rotation term
    vx = vxe * cg - vye * sg + OMEGA_EARTH * (xe * sg + ye * cg)
    vy = vxe * sg + vye * cg - OMEGA_EARTH * (xe * cg - ye * sg)
    vz = vze
    return (x, y, z, vx, vy, vz)


# ----------------------------------------------------------------------
# Public contract (matches gen_positions.py Stage 1)
# ----------------------------------------------------------------------

def propagate_positions(sats, start_utc, duration_s, step_s, out_dir):
    """
    sats: [{"norad_id": int, "name": str, "l1": str, "l2": str}, ...]
    Returns the manifest dict and writes manifest.json + positions/*.csv.
    """
    out = pathlib.Path(out_dir)
    (out / "positions").mkdir(parents=True, exist_ok=True)
    n_samples = int(duration_s // step_s) + 1

    manifest_sats = []
    for s in sats:
        elem = parse_tle(s["l1"], s["l2"])
        a = semi_major_axis(elem["mean_motion"])

        fname = f"{s['norad_id']}.csv"
        with open(out / "positions" / fname, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["t_offset_s", "x_m", "y_m", "z_m",
                        "vx_mps", "vy_mps", "vz_mps"])
            for i in range(n_samples):
                t = i * step_s
                x, y, z, vx, vy, vz = _demo_state(elem, a, t)
                w.writerow([f"{t:.1f}", f"{x:.3f}", f"{y:.3f}", f"{z:.3f}",
                            f"{vx:.6f}", f"{vy:.6f}", f"{vz:.6f}"])

        manifest_sats.append({
            "norad_id": s["norad_id"],
            "name": s.get("name", ""),
            "file": f"positions/{fname}",
            "altitude_km": round((a - EARTH_RADIUS_M) / 1000.0, 1),
            "inclination_deg": round(math.degrees(elem["inc"]), 2),
            "period_min": round(2 * math.pi * math.sqrt(a**3 / MU) / 60.0, 1),
        })

    manifest = {
        "frame": "ECEF/ITRS",
        "units": {"position": "m", "velocity": "m/s"},
        "start_utc": start_utc.isoformat(),
        "step_s": step_s,
        "num_samples": n_samples,
        "num_satellites": len(manifest_sats),
        "propagator": "demo-circular",   # real pipeline sets this to "sgp4"
        "satellites": manifest_sats,
    }
    with open(out / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    return manifest
