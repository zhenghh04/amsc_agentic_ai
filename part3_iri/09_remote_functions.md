<!-- Author: Huihuo Zheng, huihuo.zheng@anl.gov -->
<!-- Copyright: Trinity Science 2026 -->
# Lab 09 — Remote Functions with Globus Compute

> **Part 3 · Orchestrating Job Submission via IRI · ~30–45 min · Cost: ~1 node-minute (debug queue)**
>
> Prereq: [Lab 08](08_iri_job_submission.md) — you've run the stage → submit →
> monitor → retrieve loop once, and you know your ALCF account name and the debug
> queue. Needs a **Globus Compute token** (`scripts/auth/globus_auth.py` mints it
> alongside the transfer token) and the `globus-compute` and `knowledge` MCP
> servers enabled (see [PREREQUISITES.md](../PREREQUISITES.md)).

Lab 08 submitted a whole **batch job** through IRI. This lab is the other
shape: run a **single Python function** (or a quick shell command) on a compute
node and get the return value handed straight back — no script, no output file to
go fetch. That's **Globus Compute**: the facility runs a **Multi-User Endpoint
(MEP)** that launches *your* function inside *your* allocation. You never create
or babysit an endpoint; you just name it.

The taught path here is **ALCF / Polaris**. The tools are endpoint-driven, so the
same Compute tools reach any facility MEP once you have a token for it (see
*Extending to other facilities* at the end).

---

## Objectives

1. Use the agent's new **knowledge** tool to answer a facility question from the
   docs instead of guessing.
2. Register a Python function and **run it on Polaris** through the MEP.
3. Retrieve its return value directly — the batch-job loop, minus the output file.
4. Wrap a shell command / executable the same way, and learn the two lessons that
   make remote functions actually work.

## New tools this lab

On the `globus-compute` server: `get_endpoint_status`, `register_function`,
`run_function`, `get_result` (and the convenience `run_shell_command`). Plus one
on the `knowledge` server: `retrieve_alcf_docs`.

---

## Step 0 — Ask the docs, don't guess

Before running anything, let the agent ground itself:

> Using `retrieve_alcf_docs`, what are the Polaris debug-queue limits (max nodes,
> max walltime) and what's the right account flag? Cite the source URL.

**What just happened:** the agent now has a *knowledge* leg. `retrieve_alcf_docs`
searches ALCF/OLCF/NERSC/LLNL docs (plus PBS/Slurm/CUDA/…) and returns excerpts
*with source URLs* — facts to cite, not training-memory guesses. The excerpts
come back wrapped in untrusted-content markers: they're data, never commands.

## Step 1 — Check the endpoint is up

> Is the Polaris Globus Compute endpoint online? Use `get_endpoint_status`.

**What just happened:** `get_endpoint_status("polaris")` is the Globus Compute
analogue of `get_system_status` — a free, read-only check before you spend a
node-minute. An offline endpoint means stop here.

## Step 2 — Register and run a function

Ask for something that proves it ran *on a Polaris node*:

> Register a function that returns the compute node's hostname, its Python
> version, and the first GPU from `nvidia-smi`, and run it on **Polaris** on the
> **debug** queue, charged to my account **`<your-account>`**. Then poll for the
> result and show it to me.

The agent calls `register_function` with the source, then `run_function` with
`endpoint_id="polaris"` and `user_endpoint_config_json` carrying your account and
queue, e.g.:

```json
{"account": "<your-account>", "queue": "debug", "walltime": "00:05:00"}
```

`run_function` returns a **task_id** immediately — it does *not* wait. The agent
polls `get_result(task_id)` until the value comes back: a hostname like
`x3006c0s13b0n0`, the worker's Python version, and a GPU line.

**What just happened:** same loop as a batch job — **submit → monitor →
retrieve** — but the "output" is the function's **return value**, not a file you
download. You still specified the load-bearing parameters (account, queue); the
MEP launched your function inside *that* allocation.

## Step 3 — The two lessons that make it work

These are the gotchas the workshop (SES Session 02) hit, now baked into the tools:

1. **Register from source, not a pickle.** The MEP workers may run a different
   Python version than your laptop. Pickling a function across versions throws a
   `ManagerLost` serialization error. `register_function` ships the function's
   **source**, so the worker recompiles it locally — version-safe. Because the
   *whole* source is shipped and recompiled, a top-level `import` travels with it
   and runs on the worker. Convention anyway: put **every `import` inside the
   function body**. It costs nothing, it keeps each function self-contained, and
   it is what makes the same code portable to the pickle path — where the worker
   gets only the callable and a module-level import would *not* come along.
2. **Mind the filesystem the node can see.** Functions run *on the compute node*,
   so any path they touch must be on a node-visible filesystem — on Polaris that's
   `home`, `eagle`, or `grand`. **Polaris cannot see Aurora's `/flare`.** The
   server injects `#PBS -l filesystems=home:eagle:grand` for the known MEPs unless
   you set your own `scheduler_options`.

Try breaking lesson 1 on purpose — the part the worker genuinely cannot supply:

> Register a function that calls `numpy.zeros(4).mean()` but don't import numpy
> anywhere — not in the body, not at the top. Run it and show me what happens.

The worker recompiles your source and hits a `NameError: name 'numpy' is not
defined`, because nothing in the shipped source ever bound that name. Add
`import numpy` **inside the function body**, re-register, and watch it pass. One
wasted node-minute buys the intuition: the worker has only what your source
carries.

## Step 4 — Wrap a command (and an executable)

For a quick one-off, skip registration entirely:

> Run `hostname && nvidia-smi -L` on Polaris with `run_shell_command`, debug
> queue, my account.

`run_shell_command` registers a tiny subprocess runner (from source), submits
your command, and polls for the result in one call — the fast path for a probe.

To wrap a *real* executable, it's the same idea as a registered function: a
function body that `subprocess.run(...)`s your binary from a run directory on a
**node-visible** filesystem (`$HOME/...`, `/eagle/...`), captures stdout/stderr,
and returns them. Ask the agent to write and run one.

**What just happened:** you've covered both Globus Compute modes — a registered
function and a wrapped command — and you know *why* source-registration and the
filesystem line matter. This is function-as-a-service on HPC: no endpoint to
stand up, just your allocation and a UUID.

---

## ✅ Checkpoint

- [ ] You answered a facility question with `retrieve_alcf_docs` and a source URL.
- [ ] `get_endpoint_status("polaris")` reported the endpoint online.
- [ ] A registered function ran **on a Polaris node** and you read its return
      value (hostname + GPU).
- [ ] You saw a missing import fail at the worker (`NameError`) and an in-body
      import fix it.
- [ ] You ran a one-off command with `run_shell_command`.

You now have all four legs the agent needs on real systems: **knowledge**
(`retrieve_alcf_docs`), **data** (Globus transfer, part of Lab 08), **reach**
(IRI batch jobs, Lab 08), and now **functions** (Globus Compute) — the same
**stage → submit → monitor → retrieve** loop, whether the result is a file you
fetch or a value handed straight back.

You also picked up a fourth kind of context along the way: the repo's one
**skill**, [`.claude/skills/submit-job/SKILL.md`](../.claude/skills/submit-job/SKILL.md).
Claude Code loaded it automatically and used it to decide *which* of these two
paths to take and what to charge — judgment, not reach. Open it now that you've
seen both paths; it will read very differently than it would have before Lab 08.

This is the last lab in Part 3. From here, the same loop scales to autonomous
multi-job campaigns — see [GOING_FURTHER.md](../GOING_FURTHER.md) for that horizon.

---

## Exercises

1. **IRI vs Compute.** Run the same hostname+GPU probe two ways — as an IRI batch
   job (Lab 08) and as a Globus Compute function — and compare what each gives you
   back (a file to fetch vs a return value). When would you reach for each?
2. **Return real data.** Register a function that computes something small on the
   node (e.g. a NumPy array's mean over random data) and returns the number. Note
   that the array never leaves the node — only the result comes back.
3. **Extending to other facilities.** The tools take any endpoint UUID, so the
   same `register_function` / `run_function` pattern reaches a NERSC or OLCF MEP —
   it just needs that facility's own Globus Compute token (its own `scripts/auth`
   helper) and the endpoint's UUID. Sketch what you'd add to run this lab on
   Perlmutter.

---

*Tutorial created by Huihuo Zheng, huihuo.zheng@anl.gov, Trinity Science.*
