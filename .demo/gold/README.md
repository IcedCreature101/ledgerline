# Held-out tests

One file per demo ticket, asserting the behaviour the ticket says the business expects.

These are **not** part of the shipped suite — `pyproject.toml` sets `testpaths = ["tests"]`, and this
directory is dot-prefixed so pytest's default `norecursedirs` skips it either way. A plain `pytest` in a
fresh clone never sees them.

That is the point. The agent under evaluation gets the ticket and the source, exactly as an engineer
would, and has to reproduce the problem itself. These files are what we grade its answer against
afterwards — the same separation SWE-bench uses between a task and its FAIL_TO_PASS set.

Run one deliberately:

    pytest .demo/gold/test_fees_tiered.py
