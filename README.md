SERVICE TRACKER – NETWORK COMMAND PROBING & COLLECTION FRAMEWORK
===============================================================

OVERVIEW
--------

Service Tracker is a contract-driven network auditing framework designed for
quarterly checks, forensic troubleshooting, and long-term infrastructure
documentation.

The system intentionally separates command execution, data collection,
and data interpretation to prevent vendor drift, CLI incompatibilities,
and silent failures.

Currently supported platforms include:
- ArubaOS-Switch (legacy ProCurve / ArubaOS)
- Aruba CX (AOS-CX)
- Aruba APs (AOS-8 standalone)
- Aruba Controllers (limited, read-only)


ARCHITECTURE PHILOSOPHY
----------------------

1. COMMAND CONTRACTS (IMMUTABLE)

All device interaction begins with command contracts defined in YAML.

These contracts:
- Are validated against a strict JSON schema
- Explicitly define which commands are allowed
- Enforce read-only safety rules
- Are frozen once verified against live devices

If a command is not in a contract, it must never run.


2. COMMAND PROBE (EXECUTION LAYER)

The command probe:
- Executes only schema-approved commands
- Prevents unsafe commands at runtime
- Handles pagination safely
- Stores raw, unparsed artifacts
- Produces a machine-readable manifest

The probe does NOT interpret data.
It records facts exactly as returned by the device.


3. COLLECTORS (INTERPRETATION LAYER)

Collectors:
- Parse probe artifacts
- Normalize vendor-specific output
- Record capabilities instead of assumptions
- Never crash on missing or unsupported data

Collectors are downstream of probes and must match probe reality exactly.


4. CAPABILITY-AWARE DESIGN

Not all devices support the same features.

Examples:
- Aruba APs do NOT support VLAN tables
- Aruba APs do NOT support LLDP
- Aruba CX DOES support these features
- ArubaOS-Switch DOES support these features

Unsupported commands may return parse errors.
These are expected and recorded, not treated as failures.


REPOSITORY STRUCTURE
-------------------

Service Tracker/
├── collectors/
│   ├── aruba_os_switch.py
│   ├── aruba_cx_switch.py
│   └── aruba_ap.py
│
├── tools/
│   └── command_probe/
│       ├── command_probe.py
│       ├── validate_command_set.py
│       ├── command_sets/
│       │   ├── aruba_os.yaml
│       │   ├── aruba_cx.yaml
│       │   ├── aruba_ap.yaml
│       │   └── aruba_controller.yaml
│       └── output/
│
├── schemas/
│   └── command_set.schema.json
│
├── artifacts/
│   └── collector output directories
│
├── docs/
│   └── COMMAND_CONTRACTS.txt
│
└── README.txt


SUPPORTED PLATFORMS
-------------------

ARUBAOS-SWITCH (LEGACY)
- Command set: aruba_os.yaml
- Status: FROZEN
- Verified against live switch

Supported data:
- Inventory
- Interfaces
- VLANs
- LLDP
- PoE
- MAC address table


ARUBA CX (AOS-CX)
- Command set: aruba_cx.yaml
- Status: FROZEN
- Verified against live CX stack

Supported data:
- Inventory
- Interfaces
- VLANs
- LLDP
- PoE
- MAC address table


ARUBA AP (AOS-8 STANDALONE)
- Command set: aruba_ap.yaml
- Status: FROZEN
- Verified against live AP-515

Supported data:
- Version
- Uptime
- Power / PoE state

Intentionally NOT supported:
- VLAN tables
- LLDP
- Client tables
- SSID definitions (controller-only)

Parse errors for unsupported commands are expected and safe.


ARUBA CONTROLLERS (LIMITED)
- Command set: aruba_controller.yaml
- Status: Experimental / Read-only

Purpose:
- Inventory
- License visibility
- High-level WLAN information


COMMAND SET VALIDATION
---------------------

Before running any probe, command sets must be validated:

python3 tools/command_probe/validate_command_set.py \
  tools/command_probe/command_sets/aruba_os.yaml

Expected output:
[OK] Command set is valid and safe.

If validation fails, probes must NOT be run.


RUNNING A COMMAND PROBE
----------------------

Example: Aruba CX Switch

python3 tools/command_probe/command_probe.py \
  --command-set tools/command_probe/command_sets/aruba_cx.yaml \
  --host <IP_ADDRESS> \
  --username <USERNAME> \
  --password <PASSWORD>

Output includes:
- Raw artifacts per command
- probe_manifest.json
- Timestamped, UUID-based output directory


RUNNING A COLLECTOR
------------------

Example: Aruba CX Collector

python3 collectors/aruba_cx_switch.py \
  --host <IP_ADDRESS> \
  --username <USERNAME> \
  --password <PASSWORD> \
  --site PUR-MEM \
  --quarter 2025-Q1

Produces:
- Normalized artifacts
- Collector manifest
- Capability flags


FREEZING A COMMAND SET (REQUIRED)
--------------------------------

Once a command set is validated and verified:

chmod 444 tools/command_probe/command_sets/aruba_ap.yaml

This prevents:
- Accidental edits
- Schema drift
- Silent regressions


DECEMBER 2025 ARCHITECTURAL SHIFT
--------------------------------

As of December 2025:

- Command execution is contract-driven
- Collectors no longer assume feature parity
- Unsupported features are explicitly recorded
- Parse errors are expected, logged, and safe
- Raw artifacts are preserved for forensic review

This design favors correctness, repeatability,
and auditability over convenience.

