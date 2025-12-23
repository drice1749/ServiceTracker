EXPECTED FAILURE MODES
======================

The following are NOT errors:

- CLI parse errors on unsupported commands
- Empty command output
- Missing sections
- Platform-specific command rejection


THESE ARE ERRORS
----------------

- Schema validation failures
- Command execution outside a contract
- Modifying frozen contracts
- Collectors assuming data exists


PHILOSOPHY
----------

A system that hides failure is dangerous.
A system that records failure is reliable.

