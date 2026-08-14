# Part 2 — Running Claude on HPC Systems

Part 1 ran entirely on your laptop, driving the agent through built-in tools
only. Part 2 puts `claude` **directly on an HPC system** — a login node of
**Polaris**, **Perlmutter**, or **Frontier** — instead. No MCP server, no IRI:
the agent gets a real shell and drives the scheduler's own commands, the same
way you would by hand.

> **MAG is public — no tunnel needed.** Because the AmSC gateway
> (`i2-api.genesis.american-science-cloud.org`) is a public-cloud endpoint, a
> login node reaches it over normal outbound HTTPS. There is **no proxy or SSH
> tunnel to set up** — a real simplification over intranet-only gateways. The one
> caveat: if a specific login node blocks outbound 443, use the facility's HTTP
> proxy or fall back to Part 3.

> Needs an **interactive account** on one of the three systems — nothing from
> [PREREQUISITES.md](../PREREQUISITES.md) is required for this Part (that file is
> for [Part 3](../part3_iri/README.md)). Lab 05's submit step and Lab 06
> **spend real node-hours** — keep to a debug queue, 1 node, minutes.

---

## The labs

| Lab | Title | Time | Approx cost |
| --- | --- | --- | --- |
| [05](05_native_on_your_system.md) | Run Claude natively on your system + a first job | 35–50 min | ~1 node-minute |
| [06](06_scale_the_spine.md) | Scale the spine — a real training run natively | 30–45 min | ~few node-minutes |

**Order matters** — Lab 06 assumes Lab 05's setup (Claude replying on the login
node, and you know your account/queue).

## Pick one system

You only need an account on **one** of these. Everything in Part 2 is written to
work on all three; each step calls out the per-system differences:

| | Polaris (ALCF) | Perlmutter (NERSC) | Frontier (OLCF) |
| --- | --- | --- | --- |
| Login | `ssh <you>@polaris.alcf.anl.gov` | `ssh <you>@perlmutter.nersc.gov` | `ssh <you>@frontier.olcf.ornl.gov` |
| Scheduler | **PBS** (`qsub`/`qstat`) | **Slurm** (`sbatch`/`squeue`) | **Slurm** (`sbatch`/`squeue`) |
| GPU | 4× NVIDIA A100 (40 GB) | 4× NVIDIA A100 | 8× AMD MI250X GCD |
| GPU tool | `nvidia-smi` | `nvidia-smi` | `rocm-smi` |
| Debug queue | `-q debug` | `-q debug`, `-C gpu` | `-p batch -q debug` |
| Account flag | `-A <project>` | `-A <account>` | `-A <project>` |

## The one loop to learn

Both labs walk the same four-step loop every HPC workload boils down to —
just with the scheduler's own commands standing in for a tool call:

```text
   STAGE                SUBMIT               MONITOR              RETRIEVE
 put code/data   ──▶  ask the scheduler  ──▶ poll until it   ──▶ pull results /
 on the system        to run it              reaches a           read logs;
 (already there,      (qsub/sbatch, right    terminal state       on failure,
 no staging step)      account, queue)      (qstat/squeue)        read + fix)
```

Learn this loop once and every workload — the simulation, training, and inference
spine from Part 1 — is a variation on it.

## What carries over from Part 1

- **Grounded prompts + verification** — even more important when jobs cost money.
- **MCP mental model** ([Lab 02](../part1_fundamentals/02_mcp_and_tools.md)) —
  this Part deliberately has *no* MCP tools; the agent gets a general-purpose
  shell instead. Lab 05 names that trade-off explicitly.
- **The spine** — the simulation and training you ran on your laptop are the
  *same* workloads you scale here, now on real GPUs.
- **Failure triage** — the GPU-vs-host-OOM and timeout signatures from
  [Lab 03](../part1_fundamentals/03_training.md) are exactly what these native
  jobs produce.

## A note on determinism

Agents are non-deterministic — the exact wording, and sometimes the exact
sequence of commands, varies between runs even on the same prompt. There are no
fixed tool names to check against here, just shell commands
(`qsub`/`qstat` or `sbatch`/`squeue`) — judge success by the outcome (a job that
runs, a file that lands) rather than by matching a transcript.

## Looking for the other way to reach the facilities?

Part 2 gives the agent a general-purpose shell on shared infrastructure — fast,
flexible, no facility-side setup, but no boundary on what it can touch.
[Part 3 — Orchestrating Job Submission via IRI](../part3_iri/README.md) is the
opposite trade: `claude` stays on your laptop, and the facility only ever sees a
fixed, named, auditable set of tool calls — across all three systems.
[Lab 02](../part1_fundamentals/02_mcp_and_tools.md) named this same trade-off for
the `fs` server — neither is "more correct," and nothing stops you from doing
both.

Start with [Lab 05 — Run Claude natively on your system](05_native_on_your_system.md).
