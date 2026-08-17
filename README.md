<p align="center">
  <img src="assets/trinity-logo.svg" alt="Trinity Science" width="72" height="72">
</p>

# Hands-On: Agentic AI for AmSC

*Author: Huihuo Zheng, huihuo.zheng@anl.gov*<br>
*August 2026*

A hands-on tutorial for getting started with **agentic AI** as an AmSC
(American Science Cloud) user. You'll set up an AI coding agent — **Claude Code**
in **VS Code**, pointed at the **AmSC Model Access Gateway (MAG)** — and use it to
do real scientific-computing work, first on your laptop and then on real DOE HPC
systems: **Polaris** (ALCF), **Perlmutter** (NERSC), and **Frontier** (OLCF).

You describe a task in plain English. The agent reasons about it, writes code,
runs tools, submits jobs, reads the results, and iterates.

## The spine — one example, three workloads, scaled up

Instead of disconnected exercises, this track follows **three canonical HPC
workloads** — a **simulation**, a **training** run, and an **inference** run —
and *scales the same three up* through each part:

- **Part 1 — Fundamentals (laptop):** run tiny versions of all three locally to
  learn the agent loop.
- **Part 2 — Native on an HPC system:** run them on a login/compute node of your
  chosen system, driving the scheduler directly.
- **Part 3 — Orchestrating via IRI:** run them from your laptop through MCP
  tools that reach **all three facilities**.

The track has three parts:

- **Part 1 — Fundamentals** runs entirely on your **laptop**. Just a laptop, an
  editor, and a **MAG Personal Access Token** — no allocation, no HPC account.
  You drive a small simulation, a small training run, and an inference call, and
  learn how a prompt becomes a tool call.
- **Part 2 — Running Claude on HPC Systems** runs `claude` **directly on a login
  node** of Polaris, Perlmutter, or Frontier — an interactive account on one of
  them is all you need. The agent drives the scheduler's own commands
  (`qsub`/`qstat` on Polaris, `sbatch`/`squeue` on Perlmutter/Frontier).
- **Part 3 — Orchestrating Job Submission via IRI** keeps `claude` **on your
  laptop** and reaches all three facilities through bundled MCP servers instead
  (needs [PREREQUISITES.md](PREREQUISITES.md)).

Parts 2 and 3 are independent, structurally different ways to connect the agent
to real HPC systems — do either first, or both. Both spend real node-hours once
you submit something.

> **Start on your laptop.** Part 1 needs nothing but the editor + a MAG token, so
> you get real results before wiring up any HPC access. Each lab lists exactly
> what it needs.

---

## Who this is for

- **HPC / computational-science users new to agents** — you know your science and
  your systems, but "agent," "MCP," and "tool call" are new.
- **Anyone with AmSC access** who wants to drive Claude from their editor through
  MAG, and learn to make it repeatable across DOE facilities.

No prior AI/agent experience is assumed. Basic command-line comfort helps.

---

## Part 1 — Fundamentals (laptop only)

Runs entirely on your laptop with VS Code + Claude Code + MAG — no allocation,
no HPC account.

| Lab | Title | Time | Needs |
| --- | --- | --- | --- |
| [00](part1_fundamentals/00_setup_vscode_claude_mag.md) | Set up VS Code, Claude Code, and MAG | 20–30 min | A laptop; a MAG Personal Access Token |
| [01](part1_fundamentals/01_hpc_simulation.md) | The 101: drive a small HPC **simulation** | 30–40 min | Lab 00 |
| [02](part1_fundamentals/02_mcp_and_tools.md) | MCP & tools — how a prompt becomes a tool call | 20–30 min | Lab 00 |
| [03](part1_fundamentals/03_training.md) | Drive a small **training** run | 30–40 min | Lab 01 |
| [04](part1_fundamentals/04_inference.md) | Drive an **inference** run | 30–40 min | Lab 01 |

Labs 01 · 03 · 04 are the **spine** — simulation, training, inference — the same
three workloads you'll scale up in Parts 2 and 3. Lab 02 explains the tool
machinery underneath all of them.

## Part 2 — Running Claude on HPC Systems

`claude` runs **on a login node** of Polaris, Perlmutter, or Frontier — no MCP
server, no allocation-gated setup, just an interactive account on one of them.
Because MAG is a public-cloud endpoint, the login node reaches it directly — no
tunnel required. See [part2_hpc/README.md](part2_hpc/README.md) for the full intro.

| Lab | Title | Time | Approx cost |
| --- | --- | --- | --- |
| [05](part2_hpc/05_native_on_your_system.md) | Run Claude natively on your system + a first job | 35–50 min | ~1 node-min |
| [06](part2_hpc/06_scale_the_spine.md) | Scale the spine — a real training run natively | 30–45 min | ~few node-min |

## Part 3 — Orchestrating Job Submission via IRI (all three facilities)

`claude` stays **on your laptop**; reaching Polaris, Perlmutter, and Frontier
happens entirely through the bundled `alcf-iri`, `nersc-iri`, and `olcf-iri` MCP
servers' named tools. See [part3_iri/README.md](part3_iri/README.md) for the full
intro. **Do [PREREQUISITES.md](PREREQUISITES.md) first** — an account and
allocation on at least one facility, and the bundled MCP servers authenticated.

| Lab | Title | Time | Approx cost |
| --- | --- | --- | --- |
| [07](part3_iri/07_mcp_setup_and_explore.md) | Connect to ALCF/NERSC/OLCF & explore (read-only) | 20–30 min | free |
| [08](part3_iri/08_iri_job_submission.md) | IRI job submission and monitoring | 30–45 min | ~1 node-min |
| [09](part3_iri/09_data_movement.md) | Move data with Globus | 25–35 min | free |
| [10](part3_iri/10_end_to_end_across_facilities.md) | End-to-end spine across facilities (capstone) | 45–60 min | ~few node-min |

Every lab is self-contained with: **objectives · time · prerequisites · concepts
· hands-on steps · "what just happened" · a checkpoint · exercises**.

```text
Part 1 — laptop only                Part 2 — native, on your HPC system
────────────────────                ────────────────────────────────────
00 set up VS Code + Claude + MAG     05 run Claude natively + a first job
01 simulation ─┐                     06 scale the spine (training) natively
03 training ───┤ the spine
04 inference ──┘                     Part 3 — laptop + IRI/MCP (3 facilities)
02 MCP & tools (how it works)        ─────────────────────────────────────
                                     07 connect & explore (MCP setup)
                    PREREQUISITES.md  08 IRI job submission + monitor
                    (Part 3 only:     09 move data with Globus
                     account,         10 spine end-to-end across facilities
                     allocation,
                     IRI MCP servers)
```

---

## The mental model

```text
     you (plain English)
            │
            ▼
   ┌─────────────────┐     decides which tool,
   │   the agent     │────▶ with which arguments
   │  (Claude, via   │
   │   MAG gateway)  │◀──── reads the result, decides the next step
   └─────────────────┘
            │ tool call
            ▼
   ┌─────────────────┐
   │  tools the agent │  a shell, a file writer, a plotter,
   │  can call        │  and — later — HPC facilities via MCP
   └─────────────────┘
```

- An **agent** is an LLM in a loop that can *act*: read your request, call a
  tool, look at the result, decide the next step, repeat until done.
- **MCP** (Model Context Protocol) is the open standard that lets an agent
  discover and call external tools/services. (Lab 02.)
- The **spine** (simulation → training → inference) is the same three workloads
  scaled up from your laptop to real DOE systems, so nothing is a throwaway.

---

## Authentication — the two credentials

The agent uses **two different, independent credentials**, and it helps to keep
them straight from the start. Everything is token-based; there are no passwords
or long-lived API keys checked into this repo.

**1. The MAG token — lets the agent talk to the *model*.** Every part needs this.
It's a **Personal Access Token** you mint once from the AmSC Model Access Gateway
and point Claude Code at (Lab 00). It authenticates *you → the LLM*. Part 1 needs
nothing else.

**2. Facility tokens — let the agent's tools reach the *HPC systems*.** Only
Part 3 needs these. Each facility authenticates as **you** via its own flow:

| Facility (system) | Flow | Token in `.env` |
| --- | --- | --- |
| ALCF (Polaris) | Browser **Globus** OAuth2 login (`scripts/auth/alcf_iri_token.py`) | `ALCF_IRI_TOKEN` |
| NERSC (Perlmutter) | Browser **Globus** login, forced through `nersc.gov` identity | `NERSC_IRI_TOKEN` |
| OLCF (Frontier) | Manually minted **myOLCF API token** (no browser flow) | `OLCF_IRI_TOKEN` |
| Any facility (data movement) | **Globus Transfer** token (`scripts/auth/globus_auth.py`) | `GLOBUS_TRANSFER_TOKEN` |

### How it works

- **Login → `.env`.** The ALCF/NERSC helpers run a Globus NativeApp OAuth2 flow
  (a localhost-callback browser login, or a copy-paste code over SSH), then write
  the access token into **`.env` in this folder**. The Globus refresh token is
  cached under `~/.globus/`, so access tokens auto-refresh without re-logging-in
  until the refresh token itself expires. OLCF is the exception — you paste a
  portal-minted token into `.env` yourself.
- **`.env` is read fresh on every call.** Each MCP server installs a token
  provider that **re-reads `.env` on every request** rather than caching the token
  at startup. So when a token is rotated or refreshed mid-session, the running
  server picks it up automatically — no restart. Calling `authenticate()` with no
  argument simply re-reads the current token from `.env`.
- **`.env` is a real secret.** It holds a plaintext bearer token — keep it out of
  git (this repo `.gitignore`s it) and never print or share it. That's why the
  tutorial's discipline is "never read or echo `.env`."

The step-by-step setup for all of the above lives in
[PREREQUISITES.md](PREREQUISITES.md) (Part 3). Part 1 and Part 2 only ever need
the MAG token.

---

## How to work through a lab

1. Open the lab and follow the steps top to bottom.
2. Prompts to type to the agent are shown in `> quoted` blocks. **They're
   examples, not magic strings** — agents are non-deterministic; judge success by
   the outcome, not by matching the transcript.
3. Read the *"What just happened"* box after each step — that's where the actual
   learning is.
4. Hit the **Checkpoint** before moving on. Stuck? See
   [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## A few habits worth forming early

- **Ground your prompts.** Ask for *results with evidence* and tell the agent to
  say "not sure" rather than guess. Agents fill gaps with plausible text if you
  let them.
- **Verify before you trust.** Spot-check the agent's claims — re-run the
  numbers, look at the plot, read the log. Your name is on the output.
- **Mind cost on shared systems.** Every HPC lab notes an approximate cost. Keep
  test jobs to a debug queue, 1 node, a few minutes.

---

## Going further

Parts 2 and 3 already put you on real DOE systems. Beyond them, the same loop
scales to **autonomous campaigns** — many jobs run toward a goal, with stopping
criteria and a reflection pass at the end (a future Part 4). See
[GOING_FURTHER.md](GOING_FURTHER.md) for that horizon.

---

## Instructor material

Running this as a workshop? [INSTRUCTOR_NOTES.md](INSTRUCTOR_NOTES.md) has
timing, a pre-flight checklist, and an answer-key of expected agent behavior per
lab.

---

*A self-contained fundamentals track for agentic AI on the American Science Cloud.*

---

<p align="center">
  <img src="assets/trinity-logo.svg" alt="Trinity Science" width="48" height="48">
</p>

*Tutorial created by Huihuo Zheng, huihuo.zheng@anl.gov, Trinity Science.*
