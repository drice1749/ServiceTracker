SERVICE TRACKER – ARCHITECTURE OVERVIEW
======================================

Service Tracker is a contract-first network auditing system.

Its purpose is to:
- Perform quarterly network checks
- Capture defensible forensic artifacts
- Eliminate vendor CLI drift
- Prevent silent data corruption
- Separate data capture from interpretation

This system is intentionally conservative.

Speed, convenience, and feature breadth are secondary to:
- Accuracy
- Safety
- Repeatability
- Auditability


CORE DESIGN PRINCIPLES
----------------------

1. NO COMMAND MAY EXECUTE WITHOUT A CONTRACT
2. RAW DATA IS NEVER MODIFIED
3. PARSE ERRORS ARE DATA, NOT FAILURES
4. COLLECTORS MUST MATCH REALITY, NOT EXPECTATIONS
5. ONCE VERIFIED, CONTRACTS ARE FROZEN


SYSTEM LAYERS
-------------

1. Command Set (Contract Layer)
   - YAML
   - Schema validated
   - Read-only enforced
   - Frozen after verification

2. Command Probe (Execution Layer)
   - Executes commands exactly as defined
   - Captures raw CLI output
   - No parsing
   - No assumptions

3. Collector (Interpretation Layer)
   - Parses known-good outputs
   - Records capability presence/absence
   - Never crashes on missing data

4. Artifacts + Manifests (Evidence Layer)
   - UUID-based directories
   - Immutable raw output
   - Machine-readable metadata

