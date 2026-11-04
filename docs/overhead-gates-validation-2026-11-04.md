# Overhead guidance: implementation and local validation — 2026-11-04

Applies P1–P6 from the approved overhead analysis of NEXUS `29ff9ac` (inventory
`36f691a7fa141f668fad50eac04c4b4d1b7a80c93ac166b98352f1e8fc4df389`).
The benchmark observed equal functional acceptance, 8/8, with 3,626,395 NEXUS
tokens versus 1,762,824 baseline tokens. This patch does not measure savings or
establish that executors will follow the revised instructions.

## Scope and reconciliation

Implementation starts from live `main` `29ff9ac`, verified through GitHub, in a
separate worktree. The original shared checkout and other sessions remain intact.
The short entry, selective navigation, FAST/inspection paths, separate review
criteria and concise status route already in main are preserved. Differences in
the old shared checkout were not imported or overwritten. No runtime, helper,
framework, global installation, fixture, oracle or original receipt was changed.

| Proposal | Implementation | Preserved contract |
|---|---|---|
| P1 | Build: backups stay in the authorized workspace, outside test discovery | Original and regression tests remain discovered; source backup/diff retained |
| P2 | Build/Workflow: existing state is an index, artifacts referenced rather than replicated | Durable decisions, pending work, effect identity/status, authoritative reconciliation, current configuration |
| P3 | Invocation/Routes/Brainstorming/Cognitive: section links, selected technique and expansion when insufficient | Minimum operational invariants, mandatory destinations, empty fragment is not reading |
| P4 | Invocation/Policies: unavailable review recorded once per context; Review/criteria: common metadata once | DEEP independence remains required; every tracked finding field remains required |
| P5 | Build/Policies: identify coverage before repeating and capture each check exit | Critical red/green, new regressions against initial source when necessary, final validation and CLI receipt/generation gates |
| P6 | Plan: Workflow only for unresolved ownership/state/coordination | Existing plan decisions, dependencies, compatibility, recovery and opt-in CLI contracts |

The entry remains unchanged. Additional guidance can increase reference bytes;
the hypothesis is fewer unnecessary loads/actions, not a guaranteed reduction in
package size, tokens or wall time. No independent writes/tests on shared resources
were parallelized. Reducing artifacts must not weaken recovery after partial work.

## Deterministic probes executed

Baseline on the isolated base: package validator passed; Python tests ran 228,
with one skip, no failures. Bun 1.4.2 reproduced the backup issue in a temporary
workspace: an original test imports `./src/value`; copying it under `state/before/`
as `value.test.ts` caused automatic discovery and an import error (exit 1).
Renaming only the backup to `value.test.ts.txt` yielded exit 0, one pass, zero
failures, one test file. Original test SHA-256 remained
`e4a7126d4929e8be286f3285c6168a91ba474844308eda4a09c692abbf2ef454`.
A failing check followed by `cat` retained exit 1 when the check status was captured
and returned explicitly. These are local tool probes, not new inference runs.

Reproduce the backup check without any benchmark artifacts or original changes:

```sh
rtk bypass python3 - <<'PY'
from pathlib import Path
import hashlib, shutil, subprocess, tempfile

bun = shutil.which("bun")
assert bun, "Bun is required for this local probe"
with tempfile.TemporaryDirectory(prefix="nexus-backup-probe-") as directory:
    root = Path(directory)
    (root / "src").mkdir()
    (root / "src/value.ts").write_text("export const value = 17;\n")
    original = root / "value.test.ts"
    original.write_text('import { test, expect } from "bun:test";\n'
                        'import { value } from "./src/value";\n'
                        'test("original remains discovered", () => expect(value).toBe(17));\n')
    digest = hashlib.sha256(original.read_bytes()).hexdigest()
    backup = root / "state/before/value.test.ts"
    backup.parent.mkdir(parents=True)
    shutil.copy2(original, backup)
    red = subprocess.run([bun, "test"], cwd=root, capture_output=True, text=True, timeout=30)
    assert red.returncode != 0 and "Cannot find module" in red.stderr
    backup.rename(backup.with_suffix(".ts.txt"))
    green = subprocess.run([bun, "test"], cwd=root, capture_output=True, text=True, timeout=30)
    assert green.returncode == 0 and "1 pass" in green.stderr and "0 fail" in green.stderr
    assert hashlib.sha256(original.read_bytes()).hexdigest() == digest
    print("RED import error -> GREEN; original test unchanged and discovered")
PY
```

## Application scenarios reviewed against the instructions

This is a document/contract walkthrough, not executor inference or a substitute
for a future behavioral A/B. It checks whether the text permits an unsafe shortcut.

| Scenario | Required outcome under the revised text | Local assessment |
|---|---|---|
| New context, durable NDJSON decision, pending renderer | Read existing handoff and current sources; preserve decision, finish pending work | Workflow explicitly retains decision and pending work; no parallel state source |
| Remote accept occurred before local ack; outcome uncertain | Read authoritative remote identity before ack/retry; never resend based only on a summary | Workflow distinguishes saved report from remote authority |
| Config A validated; B active after restart | Revalidate affected coverage using B; old A result is insufficient | Workflow and Invocation retain configuration/context validity |
| Tenant identity, duplicate/reordered sync, conflict, tombstone/deletion | Preserve discriminating contract/failure tests; no test removed to lower counts | Build/Policies keep critical red/green, final tests and failure coverage |
| Mixed producers, partial migration and resume | Keep compatibility, bounded migration and recovery checks; no FAST bypass | Plan migration/recovery and Invocation DEEP requirements unchanged |
| DEEP review unavailable | Record pending gate and continue only independent authorized work | No self-review approval; recheck capacity on condition change |
| Tracked finding shares reviewer/target with another finding | Every tracked record keeps severity, confidence, status, evidence and provenance | Criteria table unchanged; repeated tracked fields explicitly preserved |
| Conditional section is empty or insufficient | Expand to obtain required contract; never mark empty extraction read | Invocation fallback and mandatory destinations preserved |
| Existing plan already resolves ownership/state | Continue from it without loading another workflow for step count alone | Plan now makes the unresolved state the trigger; opt-in CLI rules unchanged |

## Validation status

| Check | Result |
|---|---|
| `python3 scripts/validate.py` | Passed: metadata, local links/anchors and skills-only package |
| `python3 skills/nexus/scripts/hook_engine.py validate` | Valid: 26 hooks |
| `python3 -m unittest discover -s tests -v` | 228 tests, no failures, one skip: opt-in native host lifecycle |
| `python3 -m unittest discover -s runtime/tests -v` | 56 tests passed; loopback permission was required |
| `git diff --check` | Passed |
| Exact reproduction embedded above | RED import error -> GREEN, original unchanged/discovered |
| Per-check status probe | Failing check followed by `cat` retained exit 1 |
| Independent document/diff review | No actionable findings; anchors and quality contracts checked |

The initial runtime invocation was blocked by the sandbox's local socket policy
(three errors in HTTP test class setup, not assertions); the complete suite passed
after loopback permission. No benchmark inference was run. Review is static and
does not prove executor adherence. The effect on token/latency/throughput remains
unverified until a separately authorized A/B with immutable inputs, fresh-context
continuity and all quality gates preserved.
