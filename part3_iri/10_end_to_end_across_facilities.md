# Lab 10 — Spine End-to-End Across Facilities (Capstone)

> **Part 3 · Orchestrating Job Submission via IRI · ~45–60 min · Cost: ~a few node-minutes (debug)**
>
> Prereq: Labs 07–09. This ties the whole track together.

Now put it all together: describe a real workload in plain English and let the
agent run it end-to-end **through IRI** — write the code, stage it with Globus,
submit, monitor, retrieve, and report the number that matters. Then, if you have
more than one facility, run the **same** workload across Polaris, Perlmutter, and
Frontier and compare. When something breaks (it will), you lean on the triage loop
from Part 1. This is what agent-driven, cross-facility HPC actually feels like.

We use the **training** spine workload (a small CNN on MNIST) because it trains to
high accuracy in a couple of minutes on one GPU — small enough to be cheap, real
enough to be a genuine end-to-end run. (Swap in the simulation or your own science
if you prefer.)

---

## Objectives

1. Drive a full training run on one facility from a single natural-language brief.
2. Watch the agent handle the whole loop, including at least one self-correction.
3. (Multi-facility) Run the *same* brief on a second/third facility and compare.
4. Retrieve the result and the accuracy.

## Step 1 — Brief the run (one facility)

Give the agent the whole task at once, with the guardrails from Lab 08:

> Train a small CNN on MNIST on **<facility>** and report the final test accuracy.
> Write the PyTorch script, stage everything with Globus, and submit via IRI to
> the **debug** queue, **1 node**, **15-minute** walltime, on account
> **`<your-account>`**. Download MNIST on the compute node or stage it first — your
> call, but tell me the plan before you submit. Use the right GPU stack for the
> system (CUDA on Polaris/Perlmutter, ROCm on Frontier). Monitor to completion,
> then report the accuracy and where the outputs are.

**What just happened:** you handed off a real objective, not a step list. The agent
has to make choices — how to get the data, how to structure the script, which GPU
stack. Asking it to state the plan *before* submitting keeps you in control while
it does the work.

## Step 2 — Review the plan, then let it run

The agent proposes a plan (script + data strategy + submit parameters). Check the
load-bearing four — account, queue, nodes, walltime — plus the CUDA-vs-ROCm choice
for the target, then:

> Plan looks good. Go — stage, submit, and monitor.

It runs the Lab 08 loop for you: stage via Globus, submit via IRI, poll to a
terminal state.

**What just happened:** the same four-step loop, now carrying a real workload
through named, logged tool calls. Nothing new to learn about the mechanics — that's
the point. Once you know the loop, scale is just a bigger script.

## Step 3 — Expect a stumble, and triage it

Real runs fail the first time surprisingly often — a missing package, an OOM, a
path, a too-short walltime, or (on Frontier) a CUDA build that can't see the AMD
GPU. When it happens:

> Read the job's stderr/stdout and tell me what failed, with quoted evidence and a
> ranked fix.

The triage from [Lab 03](../part1_fundamentals/03_training.md) diagnoses it (GPU
OOM → smaller batch; host OOM → stream the data; timeout → checkpoint sooner or ask
for more walltime; wrong GPU stack → install the ROCm wheel). Then:

> Apply that fix and resubmit.

Loop until it succeeds. **This is the autonomous submit → read-log → fix → resubmit
cycle** — the same one that, scaled up, drives real campaigns in Part 4.

## Step 4 — Retrieve the result

> Report the final test accuracy, and pull the trained checkpoint and the training
> log back to my laptop (or a local facility path) with Globus.

You should see a high MNIST accuracy (~99%) and the artifacts transferred via the
Lab 09 data loop.

## Step 5 — The cross-facility payoff (if you have more than one)

Here's what three servers buys you. Run the **identical brief** on another facility:

> Now run that exact same MNIST training on **<second facility>** and give me a
> side-by-side of the two runs: accuracy, wall-clock, and any changes you had to
> make for the different system.

**What just happened:** the agent re-ran the *same objective* on a different
machine, adapting only what the system forced — the scheduler (PBS vs Slurm), the
GPU stack (CUDA vs ROCm), the launcher (`mpiexec` vs `srun`), the account. The
**science and the loop were portable; the plumbing was not** — and the agent
absorbed that difference. That's the whole reason Part 3 ships all three servers.

> Genuinely ambitious? Ask it to run the spine's *simulation, training, and
> inference* across all three facilities and assemble one comparison table. That's
> the entire track — Part 1's three workloads, Part 3's three facilities — in a
> single conversation.

---

## ✅ Checkpoint

- [ ] The agent wrote and staged a training script from your brief.
- [ ] It ran on **debug / 1 node**, charged to **your** account, via IRI.
- [ ] You hit at least one failure and resolved it via triage + resubmit.
- [ ] You retrieved the accuracy (~99%) and the artifacts with Globus.
- [ ] (Multi-facility) you ran the same brief on a second facility and compared.

🎉 **You've completed Parts 1 and 3.** You can set up an agent (Part 1), run the
simulation/training/inference spine, and now drive genuine DOE jobs end-to-end via
IRI — across Polaris, Perlmutter, and Frontier. (Part 2 — running Claude directly
on a login node — is a separate, independent path; do it too if you haven't.)

---

## Exercises

1. **Change one knob.** Ask for the same run with a different batch size or
   learning rate and compare accuracy. You're now doing *experiments* through
   conversation, on real hardware.
2. **Two nodes.** Rerun as a 2-node data-parallel job. What did the agent change
   (launch command, ranks, script)? Same loop, more scale.
3. **Portability report.** Ask the agent to write a short note listing, for MNIST
   training, exactly what differs between Polaris, Perlmutter, and Frontier
   (scheduler, GPU stack, launcher, module loads). That note is a reusable
   cross-facility cheat sheet — and a preview of the campaign knowledge Part 4
   accumulates.

---

## Where next — Part 4 (autonomous campaigns)

You've seen the autonomous cycle in miniature (submit → read log → fix → resubmit)
and the cross-facility portability that makes it powerful. **Part 4** scales it up:
multi-step campaigns with stopping criteria and invariants, the agent running many
jobs toward a goal across facilities, and reflecting on the whole campaign
afterward. See [GOING_FURTHER.md](../GOING_FURTHER.md) for the bigger picture.

Back to the [tutorial overview](../README.md).
