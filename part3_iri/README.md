# Part 3 — Orchestrating Job Submission via IRI (all three facilities)

Part 1 ran entirely on your laptop, driving the agent through built-in tools
only. Part 3 keeps `claude` **on your laptop** and reaches **Polaris (ALCF),
Perlmutter (NERSC), and Frontier (OLCF)** entirely through a fixed, named set of
tools — MCP setup, job submission, monitoring, data movement — via three bundled
IRI MCP servers. Each facility only ever sees specific, logged API calls; nothing
is installed on the shared login nodes.

> **Do [PREREQUISITES.md](../PREREQUISITES.md) first.** Part 3 needs an account
> and allocation on **at least one** facility, and that facility's IRI MCP server
> authenticated. These labs **spend real node-hours** — each one notes an
> approximate cost. Keep to a debug queue, 1 node, minutes.

## The three servers

| Server | Serves | Auth (see PREREQUISITES) |
| --- | --- | --- |
| `alcf-iri` | **Polaris** | Globus browser login (`alcf_iri_token.py`) |
| `nersc-iri` | **Perlmutter** | Globus browser login via nersc.gov (`nersc_iri_token.py`) |
| `olcf-iri` | **Frontier** | manual API token from myOLCF (compute scope) |

You don't need all three. Set up the one(s) you have; the servers you didn't
authenticate simply report "not authenticated" and are harmless. A multi-facility
user gets the full payoff in Lab 10's capstone.

---

## The labs

| Lab | Title | Time | Approx cost |
| --- | --- | --- | --- |
| [07](07_mcp_setup_and_explore.md) | Connect to ALCF/NERSC/OLCF & explore (read-only) | 20–30 min | free (no jobs) |
| [08](08_iri_job_submission.md) | IRI job submission and monitoring | 30–45 min | ~1 node-minute |
| [09](09_data_movement.md) | Move data with Globus | 25–35 min | free (transfer only) |
| [10](10_end_to_end_across_facilities.md) | Spine end-to-end across facilities (capstone) | 45–60 min | ~a few node-minutes |

**Order matters** — each lab builds on the last. Do them in sequence.

## The one loop to learn

Every lab in this Part is the same four-step loop the agent runs for you — now
identical across all three facilities:

```text
   STAGE                SUBMIT               MONITOR              RETRIEVE
 put code/data   ──▶  ask the facility   ──▶ poll until it   ──▶ pull results /
 on the system        to run it              reaches a           read logs;
 (Globus)             (right account,        terminal state      on failure,
                       queue, nodes)                              read + fix
```

Learn this loop once and every workload — the simulation, training, and inference
spine from Part 1 — is a variation on it, on any of Polaris, Perlmutter, or
Frontier.

## What carries over from Part 1 and 2

- **Grounded prompts + verification** — even more important when jobs cost money.
- **MCP mental model** — the facility tools are just MCP tools; the agent loop
  doesn't change, only what's at the edge.
- **The spine** — the simulation/training/inference you built in Part 1 is what
  you now orchestrate on real systems, and (Lab 10) the *same* workload across
  three of them.
- **Failure triage** — the OOM/timeout signatures from Part 1/2 are what these
  jobs produce; Part 3 is where the submit → read log → fix → resubmit loop earns
  its keep.

## A note on determinism and tool names

Agents are non-deterministic — the exact wording, and sometimes the sequence of
tool calls, varies between runs. The bundled servers expose fixed, named tool sets
(`submit_job`, `get_job_status`, `globus_transfer`, …), so each lab names the
tools the agent is expected to reach for. If you've swapped in a different server
(see [PREREQUISITES.md](../PREREQUISITES.md#3-the-iri-mcp-servers-configured-in-claude-code)),
its names may differ — judge success by the outcome (a job that runs, a file that
lands), not by matching a transcript.

## Looking for the other way to reach the facilities?

Part 3 keeps the agent on your laptop with a fixed, auditable tool set across
three facilities — governed, but narrower than a real shell.
[Part 2 — Running Claude on HPC Systems](../part2_hpc/README.md) is the opposite
trade: `claude` runs directly on a login node with full shell access, no
facility-side setup. Neither is "more correct," and nothing stops you from doing
both.

Start with [Lab 07 — Connect to ALCF/NERSC/OLCF & explore](07_mcp_setup_and_explore.md).

---

*Tutorial created by Huihuo Zheng, huihuo.zheng@anl.gov, Trinity Science.*
