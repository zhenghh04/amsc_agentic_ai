# Lab 03 — Drive a Small Training Run

> **Part 1 · Fundamentals · ~30–40 min · No HPC allocation required**
>
> Prereq: [Lab 01](01_hpc_simulation.md) (you've seen the write → run → read
> loop). Helpful: [Lab 02](02_mcp_and_tools.md).

Lab 01 drove a simulation; this lab drives the **second workload of the spine**:
a small **machine-learning training run**. You'll have the agent write a training
script, run it, *watch the loss curve*, read the metrics, and iterate — and when
it stumbles (it will), you'll triage the failure. In Part 2/3 this same training
run scales onto a real GPU node.

> The worked example is a **small image classifier** (a few-layer CNN or MLP on
> MNIST / sklearn digits) because it trains to high accuracy in a minute or two on
> a **CPU** — no GPU needed for Part 1. **Substitute your own model/data freely.**
> The point is the *loop*, not the FLOPs.

---

## Objectives

1. Have the agent **write and run** a training script from a plain-English brief.
2. **Read the loss/accuracy curve** and judge whether it's learning.
3. **Iterate** — change the learning rate / batch size / epochs — and compare.
4. **Triage a failure** (GPU vs host OOM) using the sample logs, so you're ready
   for the failures real jobs throw.

---

## Step 1 — Write and run the training

Describe the task; the agent writes and runs it:

> Train a small image classifier on MNIST (or sklearn digits if MNIST isn't handy)
> in PyTorch. Keep it CPU-friendly: a small CNN or MLP, batch size 64, a few
> epochs. Print the training loss each epoch and the final test accuracy. Save the
> script as `train.py` and the metrics to `metrics.json`. Run it and show me the
> real output — don't claim an accuracy you didn't measure.

**What just happened:** same agent loop as the simulation lab — *write → run →
read* — now on a training script. The "show me the real output / don't claim an
accuracy" instruction is the grounding rule again: make it produce measured
numbers, not plausible ones.

> No PyTorch? Ask the agent to `pip install torch torchvision` into a venv, or to
> fall back to scikit-learn (`MLPClassifier` on `load_digits`) which is lighter.

## Step 2 — Read the curve, not just the final number

> Plot the training loss vs epoch and save it as `loss.png`. Looking at the curve
> and the final test accuracy: is the model actually learning, is it plateauing,
> or is it overfitting? Quote the epoch-by-epoch numbers as evidence.

Open `loss.png`. A healthy run shows loss decreasing and test accuracy climbing
(MNIST should reach well above 95%). A flat loss, a rising test loss, or NaNs all
mean something specific — and naming which is the skill.

**What just happened:** you asked for an *interpretation grounded in the actual
curve*, not a verdict. Reading the loss curve is to training what checking the
CFL number was to the simulation — the domain-specific "is this real?" check.

## Step 3 — Iterate through conversation

> Re-run with the learning rate 10x higher and 10x lower, keeping everything else
> fixed. Compare the three loss curves and final accuracies in a small table.
> Which learning rate is best here, and how can you tell from the curves?

**What just happened:** you just ran a hyperparameter sweep by describing it. The
agent handles the mechanics (edit, run, collect) while you keep the scientific
judgment (which curve is best, and *why*). This is experiment-through-conversation
— and it's exactly what an autonomous campaign automates later.

## Step 4 — When it fails: triage the log

Real training jobs fail in ways that look alike but need different fixes. Two
**sample logs** ship with this tutorial in [`../samples/`](../samples/):

- [`polaris_train_ddp.o8123456`](../samples/polaris_train_ddp.o8123456) — a
  PyTorch DDP training on **Polaris** that dies with a **GPU** out-of-memory.
- [`perlmutter_preprocess.out`](../samples/perlmutter_preprocess.out) — a
  **Perlmutter** job killed for **host RAM** out-of-memory.

Point the agent at the first:

> A training job of mine failed. Read `../samples/polaris_train_ddp.o8123456` and
> tell me: what failed, the root cause, the exact lines that show it, and how to
> fix it. Don't guess — quote the evidence.

It should identify a **CUDA out-of-memory** (device capacity), quote the
`torch.cuda.OutOfMemoryError` line, and suggest: smaller batch size, AMP/mixed
precision, gradient accumulation/checkpointing, or
`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.

Now the second — a *different* failure that also says "out of memory":

> Now read `../samples/perlmutter_preprocess.out`. Is this the same kind of
> failure? Quote the lines that tell you, and give the fix.

This one is a **host RAM** OOM (`oom-kill`, exit code 137, cgroup) during data
loading — *not* a GPU problem. The fix is different: stream/shard the data instead
of loading everything into memory, fewer dataloader workers, or a high-memory
node.

**What just happened:** you exercised the **submit → read log → fix → resubmit**
loop on real-shaped failures, without spending a node-hour. Distinguishing GPU OOM
(`torch.cuda.OutOfMemoryError`) from host OOM (`oom-kill`/137) is exactly the kind
of triage you'll do constantly once the agent runs real jobs in Parts 2 and 3.

> **Verify, don't trust.** Check that the agent's "evidence" lines actually appear
> in the log at the line numbers it cites. A confident-but-wrong diagnosis is
> worse than none.

---

## ✅ Checkpoint

- [ ] The agent wrote `train.py` and ran it (real measured accuracy, not a claim).
- [ ] You have a `loss.png` and read the curve (learning / plateau / overfit).
- [ ] You compared at least two learning rates in a table.
- [ ] You triaged both sample logs and the agent distinguished **GPU** OOM from
      **host** OOM with quoted evidence and different fixes.

Then continue to [Lab 04 — inference](04_inference.md), the last spine workload.

---

## Exercises

1. **Overfit on purpose.** Shrink the training set drastically and train longer;
   watch test accuracy diverge from training accuracy on the curve. Ask the agent
   to name the fix (regularization, early stopping, more data).
2. **A third failure mode.** Write (or ask for) a log that fails a *different* way
   — a walltime timeout (`TIME LIMIT`), a `ModuleNotFoundError`, or an MPI init
   error — and have the agent triage it. Same loop, new signature.
3. **Prep for scale.** Ask the agent: *"what would change to run this same
   training on 1 GPU node of Polaris vs Perlmutter vs Frontier?"* Note the
   answers (CUDA vs ROCm, launcher, module load) — you'll use them in Part 2.

---

## Where this points

The loss curves and failure logs here are exactly what real GPU training
produces. In Part 2 the *same* training runs on a compute node; in Part 3 the
agent submits it as a job, monitors it, and triages failures with this very loop —
now spending real node-hours. You've built the muscle locally, for free.

**Next:** [Lab 04 — drive an inference run →](04_inference.md)

---

*Tutorial created by Huihuo Zheng, huihuo.zheng@anl.gov, Trinity Science.*
