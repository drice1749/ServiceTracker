RAW VS DERIVED DATA – LIFECYCLE
===============================

Service Tracker strictly separates raw data from derived data.


RAW DATA
--------

Raw data is:
- Exact CLI output
- Unparsed
- Immutable
- Timestamped
- Stored per command

Raw data is evidence.


DERIVED DATA
------------

Derived data is:
- Parsed
- Normalized
- Inferred
- Potentially lossy

Derived data is interpretation.


RULES
-----

- Raw data MUST always be preserved
- Collectors MAY fail gracefully
- Raw data is never overwritten
- Derived data must reference its source artifacts


WHY THIS MATTERS
----------------

If parsing logic is wrong:
- Raw data allows reprocessing
- Audits remain defensible
- No information is lost

