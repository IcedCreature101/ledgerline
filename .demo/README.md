# The demo fixture

This repository is a working fintech application that also carries eight planted defects. It exists so an
autonomous maintenance system can be shown doing the whole job on an unfamiliar codebase: read a ticket,
investigate, reproduce, fix, prove the fix, and open a pull request a human decides whether to merge.

## The rules the fixture has to keep

**The shipped suite is green.** All 145 tests pass on the baseline. A defect that a plain `pytest` reveals
is not a maintenance ticket, it is a broken build — and the agent would be handed its answer. Every
planted defect lives in a behaviour the shipped tests do not cover, which is what makes it realistic:
this is how production bugs actually survive to production.

**The oracle is held out.** `.demo/gold/` holds the tests that assert what each ticket says the business
expects. They are not collected by `pytest` (dot-directory, and `testpaths = ["tests"]`), and they are
never shown to the agent. They are what we grade the agent's fix against afterwards — the same separation
SWE-bench draws between a task and its FAIL_TO_PASS set.

**The ticket is the only input.** `.demo/tickets/*.json` are written the way support writes them: a
symptom, what the customer expected, what they got, and which cases still work. No file names, no
function names, no hints about the cause. Finding the code is part of the work being demonstrated.

**Each defect is independent.** Eight defects in eight areas, no shared cause. A fix for one cannot
resolve or mask another, so eight tickets are eight genuine trials rather than one trial repeated.

## The eight

| Ticket | Difficulty | Category | Area |
|---|---|---|---|
| LGR-101 | L2 | Financial/business logic | tiered fee calculation |
| LGR-102 | L2 | Financial logic — rounding | refund allocation across order lines |
| LGR-103 | L1 | Validation | IBAN corridor check at onboarding |
| LGR-104 | L2 | API/backend behaviour | idempotency-key fingerprinting |
| LGR-105 | L3 | Transaction/payment logic | partial capture against an authorization |
| LGR-106 | L1 | Date/time and reporting | statement period month-end |
| LGR-107 | L2 | Error handling | a conversion with no rate available |
| LGR-108 | L3 | Database/data handling | paging the settlement export |

Difficulty is about how much investigation the ticket needs, not about who owns it. L1 is a defect
visible in one function once you find it; L2 needs the intent of the surrounding business rule; L3 spans
more than one call and the symptom appears somewhere other than the cause.

## Running the demo again

The demo is destructive — branches get pushed and pull requests get merged, and after that the defect the
next run is meant to find is gone. `demo-baseline` is an immutable tag on the original buggy tree.

```bash
./scripts/verify_demo.sh          # is this checkout a valid baseline?
./scripts/reset_demo.sh           # restore main to the baseline
./scripts/reset_demo.sh --push    # and force it on the remote
```

`verify_demo.sh` asserts both halves at once: the shipped suite green, and every held-out test failing.
A checkout where the first fails is broken; one where the second fails has already had a defect fixed and
a run against it will find nothing to do.
