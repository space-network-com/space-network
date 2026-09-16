"""
czml.py — convert the Stage-1 ECEF traces into Cesium CZML.

Cesium consumes CZML with position samples in the ECEF (fixed) frame under
"referenceFrame": "FIXED", as [t0, x0, y0, z0, t1, x1, y1, z1, ...] where the
times are seconds offset from the document epoch. That is exactly our trace
format, so the conversion is a direct repack — no frame math needed.
"""

import csv
import pathlib
from datetime import datetime, timedelta

# Distinct colors cycled across satellites (RGBA 0-255)
_PALETTE = [
    [80, 220, 255, 255], [255, 170, 60, 255], [120, 255, 140, 255],
    [255, 110, 200, 255], [180, 150, 255, 255], [255, 235, 90, 255],
    [90, 190, 255, 255], [255, 130, 110, 255],
]


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def build_czml(manifest, out_dir):
    out = pathlib.Path(out_dir)
    start = datetime.fromisoformat(manifest["start_utc"].replace("Z", "+00:00"))
    step = manifest["step_s"]
    n = manifest["num_samples"]
    end = start + timedelta(seconds=step * (n - 1))
    avail = f"{_iso(start)}/{_iso(end)}"

    doc = [{
        "id": "document",
        "name": "LEO constellation",
        "version": "1.0",
        "clock": {
            "interval": avail,
            "currentTime": _iso(start),
            "multiplier": 60,
            "range": "LOOP_STOP",
            "step": "SYSTEM_CLOCK_MULTIPLIER",
        },
    }]

    for idx, sat in enumerate(manifest["satellites"]):
        color = _PALETTE[idx % len(_PALETTE)]
        cart = []
        with open(out / sat["file"]) as f:
            r = csv.reader(f)
            next(r)  # header
            for row in r:
                t = float(row[0])
                cart += [t, float(row[1]), float(row[2]), float(row[3])]

        label = sat.get("name") or str(sat["norad_id"])
        period_s = int(sat.get("period_min", 95) * 60)

        doc.append({
            "id": f"sat/{sat['norad_id']}",
            "name": label,
            "availability": avail,
            "label": {
                "text": label,
                "font": "11px sans-serif",
                "fillColor": {"rgba": color},
                "showBackground": True,
                "backgroundColor": {"rgba": [0, 0, 0, 140]},
                "pixelOffset": {"cartesian2": [10, 0]},
                "scale": 0.9,
            },
            "point": {
                "color": {"rgba": color},
                "pixelSize": 8,
                "outlineColor": {"rgba": [255, 255, 255, 180]},
                "outlineWidth": 1,
            },
            "path": {
                "material": {"solidColor": {"color": {"rgba": color}}},
                "width": 1.5,
                "leadTime": period_s // 2,
                "trailTime": period_s // 2,
                "resolution": step,
            },
            "position": {
                "interpolationAlgorithm": "LAGRANGE",
                "interpolationDegree": 5,
                "referenceFrame": "FIXED",
                "epoch": _iso(start),
                "cartesian": cart,
            },
        })
    return doc
