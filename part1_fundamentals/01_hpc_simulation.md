# Lab 01 — The 101: Drive a Small HPC Simulation with the Agent

> **Part 1 · Fundamentals · ~30–40 min · No HPC allocation required**
>
> Prereq: [Lab 00](00_setup_vscode_claude_mag.md) (VS Code + Claude Code + MAG).

This is the "hello world" of agentic AI for computational scientists: take a task
you already do — **running a small simulation** — and do it *with* an agent. You'll
have Claude Code write a simulation, run it, parse its output, and plot the
result, then interrogate it like a collaborator. This is the **first workload of
the spine** (simulation → training → inference); in Parts 2 and 3 you'll run the
same kind of simulation on a real DOE system.

> This lab uses a **1-D heat-diffusion solver** as the worked example because it's
> tiny, runs in a second on a laptop, and has a known analytic behavior you can
> check against. **Substitute your own science freely** — an N-body step, an SIR
> epidemic ODE, a random walk, a small Monte Carlo. The *workflow* is identical.

---

## Objectives

By the end you will have:

1. Had the agent **write and run** a small simulation from a plain-English brief.
2. Gotten a **concrete artifact** — a plot and a printed final quantity.
3. **Verified** the result against something you know (analytic limit, conservation).
4. **Iterated** — changed a parameter and re-ran — through conversation.
5. Seen the core agent loop — *write → run → read → refine* — on a real task.

---

## Start here — just describe what you want

You don't need a polished prompt. Tell the agent, in your own words, what to
simulate and what you want out of it. For example:

> I want to simulate 1-D heat diffusion on a rod. Write a small Python program
> that solves the 1-D heat equation with an explicit finite-difference scheme:
> a rod of length 1, initial temperature a hot spike in the middle, both ends
> held at 0. Run it, then plot the temperature profile at a few times and save
> the figure to a PNG. Tell me the peak temperature at the final time.

That's a good first ask: it names the physics, the method, the boundary/initial
conditions, and the two things you want back (a figure + a number). The agent
writes the code, runs it, and reports.

> No numpy/matplotlib on your laptop? Ask the agent to set up a virtual
> environment first (`python3 -m venv .venv && source .venv/bin/activate &&
> pip install numpy matplotlib`), or to use only the standard library.

## What "driving a simulation" actually involves

Your one ask covers the whole loop. A thorough run rounds it out — keep these in
mind:

| Stage | What you're checking |
| --- | --- |
| **Write** | Correct discretization? Right initial/boundary conditions? |
| **Run** | Does it execute? Any numerical blow-up (NaN/Inf)? |
| **Stability** | Explicit schemes need a CFL-type limit (here `dt ≤ dx²/2`) — did it respect it? |
| **Parse** | Extract the quantity that matters (peak temperature, total heat) |
| **Plot** | A figure that a human can sanity-check at a glance |
| **Verify** | Does it match a known limit? (heat spreads and decays; total heat with insulated ends is conserved) |

> **Scope of the agent's job:** it *writes, runs, and summarizes* to speed up
> your work. **You still own the science.** Treat its output as a fast first pass,
> not a validated result.

---

## Step 1 — Write and run the simulation

Steps 1–4 are the thorough, repeatable version of the quick "Start here" ask.

> Write a Python simulation of 1-D heat diffusion (explicit finite difference).
> Parameters: rod length L=1, N=101 grid points, diffusivity alpha=1, ends fixed
> at 0, initial condition a narrow Gaussian spike at the center. Choose a stable
> time step and integrate to t=0.05. Save the code to `heat1d.py`, run it, and
> show me the output. Don't claim it worked — show me the actual run output.

**What just happened:** the agent called its **file-writing tool** to create
`heat1d.py` and its **shell tool** to run it. Writing code and running it are
tool calls, not something the model "just does" — these are your first concrete
tool calls (the subject of [Lab 02](02_mcp_and_tools.md)). The "show me the
actual run output" instruction keeps it honest.

## Step 2 — Get the artifacts

> Plot the temperature profile at t = 0, 0.01, and 0.05 on one figure and save
> it as `heat1d.png`. Also print the peak temperature and the total heat
> (integral of T over the rod) at each of those times. Quote the actual numbers.

Open `heat1d.png` and read the printed numbers. The "quote the actual numbers"
and "save the figure" instructions are the whole game: they force the agent to
produce checkable evidence instead of asserting success.

**What just happened:** you gave the agent an *output schema* in plain English —
which figure, which numbers. Notice you didn't ask "did it work?"; you asked for
*artifacts you can inspect*. Judgment stays yours.

## Step 3 — Interrogate and verify like a collaborator

Now use the agent as a sparring partner — the questions a computational scientist
actually asks:

> - Is the scheme stable for the dt you chose? Show me the CFL number
>   (alpha·dt/dx²) and confirm it's ≤ 0.5.
> - The ends are held at 0, so heat should leak out over time. Does the total
>   heat decrease monotonically? If instead I insulate the ends (zero-flux),
>   should total heat be conserved — and is it, in your code?
> - Bump N to 401 (finer grid). Does the peak temperature at t=0.05 change much?
>   What does that tell us about grid convergence?
> - Where might this simple scheme be inaccurate, and what would you change for a
>   production run?

**What just happened:** the agent is now doing multi-step reasoning over its own
simulation — checking numerical stability, testing a conservation law, doing a
grid-convergence check. It can do this because the code and outputs are in
context and you gave it a clear scientific lens.

> **Verify, don't trust.** Re-run one of its checks yourself, or eyeball the plot.
> Heat should spread and decay; a profile that grows or oscillates wildly means
> the CFL limit was violated. Your name is on the result.

## Step 4 — Iterate and save the run

> Save a short `RUN_NOTES.md` next to the code recording: the parameters used,
> the final peak temperature and total heat, the CFL number, and the grid-
> convergence observation. Keep the code, the PNG, and the notes together in a
> `heat1d/` folder.

**What just happened:** you now have a reproducible mini-experiment — code +
figure + a notes file. That triple (code, artifact, notes) is exactly what a
real run produces, and it's what you'll scale up: in Part 2 the *same* simulation
runs on a compute node; in Part 3 the agent submits it as a job and pulls the
results back.

---

## ✅ Checkpoint

- [ ] The agent wrote `heat1d.py` and *ran* it (you saw real output, not a claim).
- [ ] You have a `heat1d.png` whose profiles spread and decay as heat should.
- [ ] The CFL number is ≤ 0.5 and you saw the stability check.
- [ ] You changed a parameter (N) and saw the effect — an experiment through
      conversation.
- [ ] You have a `heat1d/` folder with code, figure, and `RUN_NOTES.md`.

Then continue to [Lab 02 — MCP & tools](02_mcp_and_tools.md), or jump to the next
spine workload, [Lab 03 — training](03_training.md).

---

## Exercises

1. **Break the grounding on purpose.** Ask the agent something the run can't
   answer without checking (e.g., "what's the exact peak at t=0.03?") and confirm
   it *runs the code* to answer rather than guessing a number. If it guesses,
   tighten your prompt: "compute it, don't estimate."
2. **Make it unstable, then diagnose.** Ask it to deliberately pick a `dt` above
   the CFL limit, run it, and show the blow-up — then explain the fix. This is the
   "read the failure, fix it" loop you'll lean on constantly in Parts 2/3.
3. **Swap the science.** Replace the heat equation with an SIR epidemic ODE (or
   your own model). Notice the workflow — write → run → plot → verify → iterate —
   didn't change at all. That portability *is* the lesson.

---

## Why this is the right first lab

No allocation, no queue — yet it's a genuine computational-science task, and it
exercises the entire agent loop: **write code, run it, parse output, verify
against what you know, iterate.** Once you've felt how fast this is *and* where
you still have to verify, you're ready to run the other two spine workloads
(training, inference) and then scale all three onto real DOE systems.

**Next:** [Lab 02 — MCP & tools: how a prompt becomes a tool call →](02_mcp_and_tools.md)
