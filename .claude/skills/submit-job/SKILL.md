---
name: submit-job
description: Stage inputs, run a workload on a DOE facility (IRI batch job or Globus Compute function), monitor it, and report back. Use whenever the user asks to run something on Polaris, Perlmutter, or Frontier.
---

<!-- Author: Huihuo Zheng, huihuo.zheng@anl.gov -->
<!-- Copyright: Trinity Science 2026 -->

# Running a workload on a DOE facility

This repo reaches **Polaris (ALCF)**, **Perlmutter (NERSC)**, and **Frontier
(OLCF)** from your laptop through named MCP tools — nothing is installed on the
login nodes. There are **two** ways to run work; pick by shape:

| Use | When | Tools |
| --- | --- | --- |
| **IRI batch job** | A whole script / real workload in a scheduler allocation (the normal case) | `submit_job`, `get_job_status`, `read_file`, `cancel_job` on `alcf-iri` / `nersc-iri` / `olcf-iri` |
| **Globus Compute** | A Python function or quick shell probe on a compute node, result handed straight back | `register_function`, `run_function`, `run_shell_command`, `get_result` on `globus-compute` |

Both follow the same loop: **stage → submit → monitor → retrieve**. Never invent
the account, queue, or node count — those *are* the job on a shared, billed
machine. When a facility fact is unclear (queue limits, modules, the proxy), call
`retrieve_alcf_docs` and cite it rather than guessing.

---

## A. IRI batch job (the default)

1. **Generate the input locally first** and show it to the user before moving
   anything. Every HPC `run.sh` should start with `#!/bin/bash -l` (a login shell,
   so `module`/`conda` are on PATH).
2. **Stage it** to the facility with `globus_transfer` (it reliably creates the
   path and moves the file). A task ID is **not** a delivery — poll
   `globus_transfer_status(task_id)` until it reports `SUCCEEDED` before you submit
   a job that reads the staged files.
3. **Submit.** Check `get_system_status(system)` first; stop if the system is
   down. Then `submit_job` with the account, queue, nodes, and walltime the user
   gave you — do not fill them from a default. Report the **job ID** before
   monitoring. (The server charges the account you pass; there is no safe guess.)
4. **Monitor — don't babysit.** Poll `get_job_status(resource_id, job_id)` with
   backoff: ~every 10 s for the first minute, then ~30 s. Stop at a terminal state
   (completed / failed / cancelled).
5. **Report.** On success, `read_file` the stdout/stderr and quote the relevant
   lines. On failure, quote the specific error line, propose a ranked fix, and ask
   before resubmitting — never resubmit on your own.

> OLCF/Frontier has no filesystem API — read its output with a `globus_transfer`
> download instead of `read_file`.

## B. Globus Compute (a function or a quick probe)

1. **Register the function from source** with `register_function` — it ships the
   *source* so a MEP worker on a different Python version recompiles it (this is
   what avoids the `ManagerLost` serialization error). Put **every import inside
   the function body**.
2. **Run it** with `run_function(function_id, endpoint_id, args_json, kwargs_json,
   user_endpoint_config_json)`. `endpoint_id` can be `"polaris"` or `"crux"`. For a
   facility MEP you **must** pass an `account` (and usually `queue`) in
   `user_endpoint_config_json`, e.g. `{"account": "<your-account>", "queue": "debug"}`.
3. **Mind the filesystem.** Functions run on the compute node, so any path they
   touch must be on a node-visible filesystem — on Polaris that's `home`, `eagle`,
   or `grand`. **Polaris cannot see Aurora's `/flare`.** (The server adds the
   `filesystems=home:eagle:grand` scheduler line for the known MEPs automatically.)
4. **Retrieve.** `run_function` returns a `task_id` immediately — poll
   `get_result(task_id)` until it returns a value. For a one-off command,
   `run_shell_command("hostname && nvidia-smi -L", "polaris", ...)` does
   register + run + poll in one call.

---

## Workshop guardrails

Keep test runs cheap: **debug queue, 1 node, a few minutes.** Each lab notes an
approximate cost.

- **IRI batch jobs can be cancelled.** If one is stuck or misbehaving, call
  `cancel_job` — that really does stop it and stop the billing.
- **Globus Compute tasks cannot.** The SDK has no cancellation API: once a task
  is registered it runs to completion. Giving up on `get_result` only stops you
  *watching* it — the task stays queued or running and stays billed, now
  unobserved. So the limit has to be set **before** submission: put a short
  `walltime` in `user_endpoint_config` (e.g. `"walltime": "00:05:00"`) and keep
  the node count at 1. That bound is the only thing that will actually stop a
  runaway task.

## Common causes of failure

| Symptom | Likely cause |
| --- | --- |
| Job dies at exit 127 | `#!/bin/bash -l` missing, so `module`/`conda` weren't on PATH |
| `ManagerLost` / serialization error (Globus Compute) | function pickled across Python versions — register from source |
| File not found on the compute node | path is on a filesystem the node can't see (e.g. `/flare` from Polaris) |
| Auth / 401 | token expired — re-run the relevant `scripts/auth/*.py` (or `globus_auth.py ensure_valid` for compute) |
| Wrong partition / burned allocation | account or queue was guessed instead of asked for |

---

*Skill for the tutorial "Hands-On: Agentic AI for AmSC" — Huihuo Zheng, Trinity Science.*
