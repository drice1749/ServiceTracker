# collectors/aruba_ap.py

import json
import re
from datetime import datetime
from pathlib import Path


COLLECTOR_NAME = "aruba_ap"
COLLECTOR_VERSION = "1.1"


def _load_artifacts(artifact_dir: Path):
    artifacts = {}
    for path in artifact_dir.glob("*.txt"):
        artifacts[path.name] = path.read_text(errors="ignore")
    return artifacts


def _strip_prompt_lines(text: str):
    """
    Removes CLI prompt lines like:
    bc:9f:e4:c3:f2:82#
    """
    cleaned = []
    for line in text.splitlines():
        if re.match(r"^[0-9a-f]{2}(:[0-9a-f]{2}){5}#", line.strip(), re.IGNORECASE):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def _parse_inventory(text: str):
    inventory = {
        "os_version": None,
        "model": None,
        "uptime": None,
    }

    if not text:
        return inventory

    # Model + OS version
    m = re.search(r"MODEL:\s*([^)]+)\).*Version\s+([\w\.\-]+)", text)
    if m:
        inventory["model"] = m.group(1).strip()
        inventory["os_version"] = m.group(2).strip()

    # Uptime
    u = re.search(r"AP uptime is (.+)", text)
    if u:
        inventory["uptime"] = u.group(1).strip()

    return inventory


def _parse_power(text: str):
    power = {}

    if not text:
        return power

    text = _strip_prompt_lines(text)

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("----"):
            continue
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        power[key.strip()] = value.strip()

    return power


def run_collector(artifact_root: str):
    artifact_root = Path(artifact_root)
    artifacts_dir = artifact_root / "artifacts"

    artifacts = _load_artifacts(artifacts_dir)

    capabilities = {
        "inventory": "not_supported",
        "power": "not_supported",
        "interfaces": "not_supported",
        "vlans": "not_supported",
        "lldp": "not_supported",
        "clients": "not_supported",
        "ssids": "not_supported",
        "mac_table": "not_supported",
    }

    inventory = {}
    power = {}
    parse_notes = []

    # INVENTORY
    inv_text = artifacts.get("inventory_1.txt")
    if inv_text:
        inventory = _parse_inventory(inv_text)
        capabilities["inventory"] = "supported"

    # POWER
    power_text = artifacts.get("poe_1.txt")
    if power_text:
        power = _parse_power(power_text)
        capabilities["power"] = "supported"

    manifest = {
        "collector": COLLECTOR_NAME,
        "collector_version": COLLECTOR_VERSION,
        "collected_at": datetime.utcnow().isoformat() + "Z",
        "capabilities": capabilities,
        "parse_notes": parse_notes,
        "inventory": inventory,
        "power": power,
    }

    manifest_path = artifact_root / "collector_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print("[OK] Aruba AP collection complete")
    print(f"     Manifest: {manifest_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: aruba_ap.py <artifact_directory>")
        sys.exit(1)

    run_collector(sys.argv[1])
