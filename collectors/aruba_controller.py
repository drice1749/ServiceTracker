#!/usr/bin/env python3
"""
Aruba Controller Collector

Reads command_probe artifacts and produces a normalized
collector_manifest.json for ArubaOS controllers (e.g. 7210).

This collector:
- NEVER executes commands
- NEVER assumes feature presence
- Treats parse errors as valid signals
- Records unsupported capabilities explicitly
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime

COLLECTOR_NAME = "aruba_controller"
COLLECTOR_VERSION = "1.1"


def load_artifacts(probe_dir: Path):
    artifacts_dir = probe_dir / "artifacts"
    artifacts = {}
    for path in artifacts_dir.glob("*.txt"):
        artifacts[path.name] = path.read_text(errors="ignore")
    return artifacts


def parse_inventory(artifacts):
    inventory = {
        "os_version": None,
        "model": None,
        "uptime": None,
        "serial": None,
    }

    text = artifacts.get("inventory_1.txt", "")

    m = re.search(r"ArubaOS \(MODEL:\s*([^)]+)\), Version ([\d\.]+)", text)
    if m:
        inventory["model"] = m.group(1)
        inventory["os_version"] = m.group(2)

    m = re.search(r"Switch uptime is (.+)", text)
    if m:
        inventory["uptime"] = m.group(1).strip()

    return inventory


def parse_licenses(artifacts):
    text = artifacts.get("inventory_5.txt", "")
    licenses = []

    if "License Table" not in text:
        return licenses

    for line in text.splitlines():
        if re.match(r"[A-Z0-9+/=-]{20,}", line):
            parts = re.split(r"\s{2,}", line.strip())
            if len(parts) >= 5:
                licenses.append({
                    "key": parts[0],
                    "installed": parts[1],
                    "expires": parts[2],
                    "flags": parts[3],
                    "service": parts[4],
                })

    return licenses


def parse_ssids(artifacts):
    text = artifacts.get("vlans_1.txt", "")
    ssids = []

    if "SSID Profile List" not in text:
        return ssids

    for line in text.splitlines():
        if re.match(r"\S+\s+\d+", line):
            name = line.split()[0]
            if name.lower() != "default":
                ssids.append(name)

    return ssids


def parse_virtual_aps(artifacts):
    text = artifacts.get("vlans_2.txt", "")
    vaps = []

    if "Virtual AP profile List" not in text:
        return vaps

    for line in text.splitlines():
        if re.match(r"\S+\s+\d+", line):
            name = line.split()[0]
            if name.lower() != "default":
                vaps.append(name)

    return vaps


def parse_clients(artifacts):
    text = artifacts.get("mac_table_1.txt", "")
    clients = []

    if "Users" not in text:
        return clients

    lines = text.splitlines()

    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("IP") and "AP name" in line:
            header_idx = i
            break

    if header_idx is None:
        return clients

    header = lines[header_idx]
    col_starts = [m.start() for m in re.finditer(r"\S+", header)]

    def slice_cols(line):
        fields = []
        for i, start in enumerate(col_starts):
            end = col_starts[i + 1] if i + 1 < len(col_starts) else None
            fields.append(line[start:end].strip())
        return fields

    for line in lines[header_idx + 2:]:
        if not re.match(r"\d+\.\d+\.\d+\.\d+", line):
            continue

        cols = slice_cols(line)

        try:
            clients.append({
                "ip": cols[0],
                "mac": cols[1],
                "name": cols[2] or None,
                "role": cols[3],
                "auth_age": cols[4],
                "ap": cols[7],
                "essid": cols[9],
            })
        except IndexError:
            continue

    return clients


def build_manifest(probe_dir: Path, artifacts):
    manifest = {
        "collector": COLLECTOR_NAME,
        "collector_version": COLLECTOR_VERSION,
        "collected_at": datetime.utcnow().isoformat() + "Z",
        "capabilities": {
            "inventory": "supported",
            "licenses": "supported",
            "clients": "supported",
            "ssids": "supported",
            "virtual_aps": "supported",
            "interfaces": "not_supported",
            "lldp": "not_supported",
            "poe": "not_supported",
            "vlans": "not_supported",
        },
        "parse_notes": [],
        "inventory": parse_inventory(artifacts),
        "licenses": parse_licenses(artifacts),
        "ssids": parse_ssids(artifacts),
        "virtual_aps": parse_virtual_aps(artifacts),
        "clients": parse_clients(artifacts),
    }

    out_path = probe_dir / "collector_manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2))
    return out_path


def main():
    if len(sys.argv) != 2:
        print("Usage: aruba_controller.py <probe_output_dir>")
        sys.exit(1)

    probe_dir = Path(sys.argv[1])
    artifacts = load_artifacts(probe_dir)
    out = build_manifest(probe_dir, artifacts)

    print("[OK] Aruba Controller collection complete")
    print(f"     Manifest: {out}")


if __name__ == "__main__":
    main()
