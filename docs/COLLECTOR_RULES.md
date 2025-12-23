COLLECTOR DESIGN RULES
=====================

Collectors operate ONLY on probe artifacts.

They must NEVER:
- Execute live commands
- Assume feature presence
- Crash on missing output
- Modify raw data


COLLECTOR RESPONSIBILITIES
--------------------------

- Parse only known-good outputs
- Detect unsupported capabilities
- Record "not supported" explicitly
- Produce normalized artifacts
- Emit a collector_manifest.json


CAPABILITY-BASED THINKING
------------------------

Collectors must answer:
- Does this device support X?
Not:
- Should this device support X?

Parse errors are expected and valid.

