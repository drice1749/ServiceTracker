#!/usr/bin/env python3
"""
Derive AP → Client Correlation

Consumes:
- Aruba AP collector_manifest.json
- Aruba Controller collector_manifest.json

Produces:
- derived/ap_client_correlation.json

Rules:
- Never assumes AP naming consistency
- Never fails silently
- Always emits output
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def load_manifest(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing manifest: {path}")
    return json.loads(path.read_text())


def main():
    if len(sys.argv) != 3:
        print("Usage: derive_ap_client_map.py <ap_probe_dir> <controller_probe_dir>")
        sys.exit(1)

    ap_dir = Path(sys.argv[1])
    ctrl_dir = Path(sys.argv[2])

    ap_manifest = load_manifest(ap_dir / "collector_manifest.json")
    ctrl_manifest = load_manifest(ctrl_dir / "collector_manifest.json")

    result = {
        "derived_at": datetime.utcnow().isoformat() + "Z",
        "source": {
            "ap_collector": ap_manifest.get("collector"),
            "ap_version": ap_manifest.get("collector_version"),
            "controller_collector": ctrl_manifest.get("collector"),
            "controller_version": ctrl_manifest.get("collector_version"),
        },
        "summary": {
            "aps_seen": 0,
            "clients_seen": len(ctrl_manifest.get("clients", [])),
            "clients_correlated": 0,
        },
        "notes": [],
        "aps": {},
    }

    # AP identity currently unavailable → record explicitly
    result["notes"].append(
        "AP collector does not yet emit AP names compatible with controller client AP fields"
    )

    # Still record raw clients grouped by reported AP name
    for client in ctrl_manifest.get("clients", []):
        ap_name = client.get("ap") or "UNKNOWN"
        result["aps"].setdefault(ap_name, []).append(client)

    result["summary"]["aps_seen"] = len(result["aps"])

    # Output path
    derived_dir = ap_dir.parent / "derived"
    derived_dir.mkdir(parents=True, exist_ok=True)

    out_path = derived_dir / "ap_client_correlation.json"
    out_path.write_text(json.dumps(result, indent=2))

    print("[OK] Derived AP → client correlation")
    print(f"     Output: {out_path}")


if __name__ == "__main__":
    main()
